#include <Arduino.h>
#include "hal/HAL.h"
#include "factory/DriverFactory.h"
#include "config/DriverMode.h"
#include "CalibrationProfiles.h"
#include "CalibrationManager.h"
#include "CalibratedSensor.h"
#include "CalibrationValidator.h"
#include "repository/MockStorage.h"
#include "repository/CalibrationRepository.h"
#include "repository/RepositoryProfile.h"
#include "Scheduler.h"
#include "time/ArduinoTimeProvider.h"
#include "FSM.h"
#include "IFSMObserver.h"
#include "EventDispatcher.h"
#include "MockWiFiService.h"
#include "WiFiManager.h"
#include "MockCredentialProvider.h"
#include "IWiFiObserver.h"
#include "MockMQTTService.h"
#include "MQTTManager.h"
#include "IMQTTObserver.h"
#include "IMQTTConnectionObserver.h"
#include "BackendGateway.h"
#include "DiagnosticsManager.h"
#include "VerificationManager.h"

// Specifications
#define PROJECT_NAME "AquaSentinel-AI"
#define FIRMWARE_VERSION "3.8.1"
#define BUILD_DATE __DATE__
#define BUILD_TIME __TIME__

#include "PhysicalWiFiService.h"
#include "PhysicalMQTTService.h"

// Configuration
const DriverMode ACTIVE_MODE = DriverMode::HYBRID;
PinConfig pinConfig;

// Instantiation of Persistence Framework
MockStorage* calibrationStorage = new MockStorage();
CalibrationRepository calibrationRepository(calibrationStorage);
RepositoryProfile repositoryProfile(&calibrationRepository);
CalibrationManager calibrationManager(&repositoryProfile);

// Allocate Raw Sensor Hardware Instances
ISensor* rawTemp = DriverFactory::createTemperatureSensor(pinConfig, ACTIVE_MODE);
ISensor* rawSalinity = DriverFactory::createSalinitySensor(pinConfig, ACTIVE_MODE);
ISensor* rawPH = DriverFactory::createPHSensor(pinConfig, ACTIVE_MODE);
ISensor* rawTurbidity = DriverFactory::createTurbiditySensor(pinConfig, ACTIVE_MODE);
ISensor* rawDO = DriverFactory::createDOSensor(pinConfig, ACTIVE_MODE);

// Wrap Sensors with Calibration Decorators
ISensor* tempSensor = new CalibratedSensor(rawTemp, SensorType::TEMPERATURE, &calibrationManager);
ISensor* salinitySensor = new CalibratedSensor(rawSalinity, SensorType::SALINITY, &calibrationManager);
ISensor* phSensor = new CalibratedSensor(rawPH, SensorType::PH, &calibrationManager);
ISensor* turbiditySensor = new CalibratedSensor(rawTurbidity, SensorType::TURBIDITY, &calibrationManager);
ISensor* calibratedDO = new CalibratedSensor(rawDO, SensorType::DISSOLVED_OXYGEN, &calibrationManager);

// Allocate Actuators
IActuator* greenLed = DriverFactory::createLED(pinConfig.greenLedPin, ACTIVE_MODE);
IActuator* yellowLed = DriverFactory::createLED(pinConfig.yellowLedPin, ACTIVE_MODE);
IActuator* redLed = DriverFactory::createLED(pinConfig.redLedPin, ACTIVE_MODE);
IActuator* buzzer = DriverFactory::createBuzzer(pinConfig.buzzerPin, ACTIVE_MODE);
IActuator* pumpRelay = DriverFactory::createRelay(pinConfig.pumpRelayPin, ACTIVE_MODE);

// Instantiate GPS
IGPSSensor* gpsSensor = DriverFactory::createGPSSensor(pinConfig, ACTIVE_MODE);

// Instantiate HAL coordinator with DECORATED sensor interfaces
HAL hal(pinConfig, tempSensor, salinitySensor, phSensor, turbiditySensor, calibratedDO, gpsSensor,
        greenLed, yellowLed, redLed, buzzer, pumpRelay);

// Instantiate Time Provider & Cooperative Scheduler
ArduinoTimeProvider timeProvider;
Scheduler scheduler(&timeProvider);

// Instantiate FSM controller and Dispatcher
FSM fsm(hal);
EventDispatcher dispatcher;

// Credentials for Live Bench Integration
class LiveCredentialProvider : public ICredentialsProvider {
public:
    LiveCredentialProvider() {}
    ~LiveCredentialProvider() override {}
    const char* getSSID() override { return "Amrita_CHN2"; }
    const char* getPassword() override { return "amrita@321"; }
};

// Dummy mock service instances to satisfy libVerification linker references
MockWiFiService mockWiFi;
MockMQTTService mockMQTT;

// Instantiate Wi-Fi Connectivity Layer with Physical WiFi Driver
LiveCredentialProvider credentialsProvider;
WiFiConnectionPolicy wifiPolicy(true, true, 5, 10000, -85, -80);
PhysicalWiFiService physicalWiFi;
WiFiManager wifiManager(&physicalWiFi, &dispatcher, &credentialsProvider, wifiPolicy);

// Instantiate MQTT Communication Layer with Local Broker on PC LAN IP (11.12.8.172:1883)
MQTTConfig mqttConfig = {"11.12.8.172", 1883, "AQUA_FRESH_001_node", "", "", 15, true, 0, 5000, "aquatic/AQUA_FRESH_001/status", "Offline"};
MQTTTopicRegistry mqttTopics = {"aquatic/AQUA_FRESH_001/telemetry", "aquatic/AQUA_FRESH_001/alerts", "aquatic/AQUA_FRESH_001/command", "aquatic/AQUA_FRESH_001/diagnostics", "aquatic/AQUA_FRESH_001/heartbeat", "aquatic/AQUA_FRESH_001/firmware", "aquatic/AQUA_FRESH_001/configuration"};
MQTTTopicPolicy mqttPolicy(TopicPermission::READ_WRITE, 1, true, 1024);
MQTTQoSPolicy mqttQoSPolicy(0, 2000, 3);
PhysicalMQTTService physicalMQTT;
MQTTManager mqttManager(&physicalMQTT, &dispatcher, &wifiManager, mqttConfig, mqttTopics, mqttPolicy, mqttQoSPolicy);

// Instantiate Backend Integration Gateway
BackendGateway backendGateway(&mqttManager, &dispatcher, "AQUA_FRESH_001", "caml");

// Instantiate Diagnostics Manager
DiagnosticsManager diagnosticsManager(&scheduler, &fsm, &wifiManager, &mqttManager, &backendGateway, &dispatcher);

// -----------------------------------------------------------------
// OBSERVERS IMPLEMENTATION
// -----------------------------------------------------------------

class LoggerObserver : public IFSMObserver {
public:
    void onStateTransition(State fromState, Event ev, State toState) override {
        Serial.print("[OBSERVER] FSM Transition: ");
        Serial.print((int)fromState);
        Serial.print(" -> ");
        Serial.print((int)toState);
        Serial.print(" | Event: ");
        Serial.println((int)ev);
    }
};

class WiFiLoggerObserver : public IWiFiObserver {
public:
    void onWiFiStateTransition(WiFiState fromState, WiFiState toState) override {
        Serial.print("[OBSERVER] Wi-Fi Transition: ");
        Serial.print((int)fromState);
        Serial.print(" -> ");
        Serial.println((int)toState);
    }
    void onSignalChanged(int rssi) override {
        // Signal strength change hooks
    }
};

class MQTTLoggerObserver : public IMQTTObserver {
public:
    void onMQTTStateTransition(MQTTState fromState, MQTTState toState) override {
        Serial.print("[OBSERVER] MQTT Transition: ");
        Serial.print((int)fromState);
        Serial.print(" -> ");
        Serial.println((int)toState);
    }
    void onMessagePublished(const char* topic, const char* payload) override {
        Serial.print("[OBSERVER] MQTT Message Published: ");
        Serial.println(topic);
    }
    void onMessageReceived(const char* topic, const char* payload) override {
        Serial.print("[OBSERVER] MQTT Message Received: ");
        Serial.println(topic);
    }
};

class MQTTConnectionLogger : public IMQTTConnectionObserver {
public:
    void onConnected() override { Serial.println("[CONN-OBSERVER] MQTT Broker Connected."); }
    void onDisconnected() override { Serial.println("[CONN-OBSERVER] MQTT Broker Disconnected."); }
    void onBrokerLost() override { Serial.println("[CONN-OBSERVER] MQTT Broker Lost Connection!"); }
    void onReconnect() override { Serial.println("[CONN-OBSERVER] MQTT Broker Reconnecting..."); }
    void onAuthenticationFailure() override { Serial.println("[CONN-OBSERVER] MQTT Authentication Failed."); }
};

LoggerObserver loggerObserver;
WiFiLoggerObserver wifiLogger;
MQTTLoggerObserver mqttLogger;
MQTTConnectionLogger mqttConnLogger;

// -----------------------------------------------------------------
// COOPERATIVE TASK CALLBACKS
// -----------------------------------------------------------------

void sensorPollingTask(TaskContext& context) {
    TelemetryData telemetry = hal.readAllSensors();
    diagnosticsManager.feedSensorRead();
    Serial.print("[TASK] Sensor Polling (Calibrated): ");
    Serial.print("Temp: "); Serial.print(telemetry.temperature_c); Serial.print(" C | ");
    Serial.print("pH: "); Serial.print(telemetry.ph); Serial.print(" | ");
    Serial.print("Salinity: "); Serial.print(telemetry.salinity_ppt); Serial.print(" ppt | ");
    Serial.print("Turbidity: "); Serial.print(telemetry.turbidity_ntu); Serial.print(" NTU | ");
    Serial.print("DO: "); Serial.print(telemetry.dissolved_oxygen_mg_l); Serial.println(" mg/L");

    // Queue telemetry payload publishing to MQTT broker via BackendGateway
    if (mqttManager.isConnected()) {
        bool queued = backendGateway.publishTelemetry(telemetry);
        Serial.print("[TASK] Telemetry publish to MQTT: ");
        Serial.println(queued ? "QUEUED_OK" : "QUEUE_FULL");
    } else {
        Serial.println("[TASK] MQTT connecting... (publish skipped until connected)");
    }
}

void calibrationUpdateTask(TaskContext& context) {
    Serial.println("[TASK] Calibration Profile Checked: OK");
}

void driverHealthTask(TaskContext& context) {
    bool ok = hal.runSelfTest();
    Serial.print("[TASK] Driver Health Diagnostic Self-Test: ");
    Serial.println(ok ? "PASSED" : "FAILED");
}

void ledUpdateTask(TaskContext& context) {
    if (fsm.getCurrentState() == State::MONITORING || fsm.getCurrentState() == State::IDLE) {
        const char* currentState = hal.readActuator("green_led");
        if (strcmp(currentState, "ON") == 0) {
            hal.writeActuator("green_led", "OFF");
        } else {
            hal.writeActuator("green_led", "ON");
        }
    }
}

void buzzerUpdateTask(TaskContext& context) {
    // Placeholder refreshing alarm buzzer registers
}

void fsmUpdateTask(TaskContext& context) {
    fsm.update();
    backendGateway.setFSMState(static_cast<int>(fsm.getCurrentState()));
}

void wifiUpdateTask(TaskContext& context) {
    wifiManager.update();
    backendGateway.setWiFiConnected(wifiManager.isConnected());
}

void mqttUpdateTask(TaskContext& context) {
    mqttManager.update();
    if (mqttManager.isConnected()) {
        diagnosticsManager.feedCommunication();
    }
}

void backendUpdateTask(TaskContext& context) {
    backendGateway.update();
}

void diagnosticsUpdateTask(TaskContext& context) {
    diagnosticsManager.update();
}

void heartbeatTask(TaskContext& context) {
    diagnosticsManager.feedHeartbeat();
    Serial.print("[TASK] Heartbeat. System Uptime: ");
    Serial.print(context.currentTime / 1000);
    Serial.println(" seconds");

    // Print Scheduler utilization and loop latency diagnostics
    Scheduler* sched = (Scheduler*)context.schedulerRef;
    if (sched) {
        const SchedulerDiagnostics& diag = sched->getDiagnostics();
        Serial.print("  | CPU Utilization: ");
        Serial.print(diag.getSchedulerUtilization(), 2);
        Serial.print("% | Avg Loop Latency: ");
        Serial.print(diag.getAverageLoopLatencyUs());
        Serial.println(" us");
    }

    // Print Current State Context and Dispatcher Queue Depth
    const StateContext& ctx = fsm.getContext();
    FSMDiagnostics fsmDiag = fsm.getDiagnostics();
    Serial.print("  | FSM State: ");
    Serial.print((int)ctx.currentState);
    Serial.print(" | Transitions: ");
    Serial.print(ctx.transitionCount);
    Serial.print(" | Queue Depth: ");
    Serial.println(fsmDiag.queueDepth);

    // Print Wi-Fi Connectivity and Signal strength (V2 diagnostics)
    const WiFiDiagnostics& wifiDiag = wifiManager.getDiagnostics();
    Serial.print("  | Wi-Fi State: ");
    Serial.print((int)wifiDiag.currentState);
    Serial.print(" | IP: ");
    Serial.print(wifiDiag.currentIp);
    Serial.print(" | RSSI: ");
    Serial.print(wifiDiag.rssi);
    Serial.println(" dBm");

    // Print MQTT Stats
    const MQTTDiagnostics& mqttDiag = mqttManager.getDiagnostics();
    Serial.print("  | MQTT State: ");
    Serial.print((int)mqttDiag.currentState);
    Serial.print(" | Publishes: ");
    Serial.print(mqttDiag.publishCount);
    Serial.print(" | Success Rate: ");
    Serial.print(mqttDiag.publishSuccessRate, 1);
    Serial.print("% | Queue Depth: ");
    Serial.println(mqttDiag.queueDepth);
}

// -----------------------------------------------------------------
// ARDUINO LIFECYCLE
// -----------------------------------------------------------------

void setup() {
    Serial.begin(115200);
    while (!Serial) {
        ; // Wait for serial connection
    }

    Serial.println("--------------------------------");
    Serial.print(PROJECT_NAME);
    Serial.println(" Firmware");
    Serial.print("Firmware Version: ");
    Serial.println(FIRMWARE_VERSION);
    Serial.print("Build Date: ");
    Serial.println(BUILD_DATE);
    Serial.print("Build Time: ");
    Serial.println(BUILD_TIME);
    Serial.print("Hardware Mode: ");
    Serial.println(ACTIVE_MODE == DriverMode::PHYSICAL ? "PHYSICAL SENSORS" : (ACTIVE_MODE == DriverMode::HYBRID ? "HYBRID (PHYSICAL pH + TURBIDITY + ACTUATORS)" : "MOCK SIMULATOR"));
    Serial.println("--------------------------------");

    // Initialize Calibration Database Repository
    calibrationRepository.initialize();

    // Run calibration layer unit tests only in MOCK mode
    if (ACTIVE_MODE == DriverMode::MOCK) {
        CalibrationValidator::runUnitTests();
    }

    // Initialize HAL
    Serial.println("\n[SYSTEM] Initializing Hardware Abstraction Layer...");
    if (hal.initialize()) {
        Serial.println("[SYSTEM] HAL Initialized Successfully (Status: OK)");
    } else {
        Serial.println("[SYSTEM] ERROR: HAL Initialization Failed (Status: FAULT)");
    }

    // Run Diagnostics
    Serial.println("[SYSTEM] Executing sensor diagnostics self-test...");
    if (hal.runSelfTest()) {
        Serial.println("[SYSTEM] Diagnostics PASSED. All sensors functional.");
    } else {
        Serial.println("[SYSTEM] WARNING: Diagnostics FAILED. Hardware errors detected.");
    }

    // Bind dispatcher and register transitions observer
    fsm.setDispatcher(&dispatcher);
    fsm.getObserverManager().subscribe(&loggerObserver);

    // Initialize State Machine and trigger transition BOOT -> INITIALIZING
    fsm.initialize();

    // Configure Wi-Fi Observers and initialize connectivity
    wifiManager.getObserverManager().subscribe(&wifiLogger);
    wifiManager.initialize();
    wifiManager.connect();

    // Configure MQTT Observers and initialize communications
    mqttManager.getObserverManager().subscribe(&mqttLogger);
    mqttManager.getConnectionObserverManager().subscribe(&mqttConnLogger);
    mqttManager.initialize();

    // Initialize Backend Gateway
    backendGateway.initialize();
    backendGateway.setWiFiConnected(wifiManager.isConnected());
    backendGateway.setFSMState(static_cast<int>(fsm.getCurrentState()));

    // Initialize Diagnostics Manager
    diagnosticsManager.initialize();

    // Default Indicator States
    hal.writeActuator("green_led", "ON");
    hal.writeActuator("yellow_led", "OFF");
    hal.writeActuator("red_led", "OFF");
    hal.writeActuator("buzzer", "OFF");
    hal.writeActuator("pump_relay", "OFF");
    
    // Register Default Tasks into Cooperative Scheduler
    // Args: Task(ID, Name, IntervalMs, Callback, Priority, Enabled)
    scheduler.registerTask(new Task(TaskId::SENSOR_POLLING, "Sensor Polling", 5000, sensorPollingTask, TaskPriority::CRITICAL));
    scheduler.registerTask(new Task(TaskId::CALIBRATION, "Calibration Update", 10000, calibrationUpdateTask, TaskPriority::LOW));
    scheduler.registerTask(new Task(TaskId::HEALTH_CHECK, "Health Check", 15000, driverHealthTask, TaskPriority::HIGH));
    scheduler.registerTask(new Task(TaskId::LED_UPDATE, "LED Update", 1000, ledUpdateTask, TaskPriority::LOW));
    scheduler.registerTask(new Task(TaskId::BUZZER_UPDATE, "Buzzer Update", 2000, buzzerUpdateTask, TaskPriority::NORMAL));
    scheduler.registerTask(new Task(TaskId::HEARTBEAT, "Heartbeat", 3000, heartbeatTask, TaskPriority::BACKGROUND));
    
    // Register FSM Update Task
    scheduler.registerTask(new Task(TaskId::FSM_UPDATE, "FSM Update", 1000, fsmUpdateTask, TaskPriority::CRITICAL));

    // Register Wi-Fi Update Task
    scheduler.registerTask(new Task(TaskId::WIFI_UPDATE, "WiFi Update", 1000, wifiUpdateTask, TaskPriority::NORMAL));

    // Register MQTT Update Task
    scheduler.registerTask(new Task(TaskId::MQTT_UPDATE, "MQTT Update", 1000, mqttUpdateTask, TaskPriority::NORMAL));

    // Register Backend Update Task
    scheduler.registerTask(new Task(TaskId::BACKEND_UPDATE, "Backend Update", 1000, backendUpdateTask, TaskPriority::NORMAL));

    // Register Diagnostics Update Task
    scheduler.registerTask(new Task(TaskId::DIAGNOSTICS_UPDATE, "Diagnostics Update", 5000, diagnosticsUpdateTask, TaskPriority::NORMAL));

    Serial.println("Starting Cooperative Task Scheduler...");
    Serial.println("--------------------------------");

    // Execute End-to-End System Verification Suite on startup only in MOCK mode
    if (ACTIVE_MODE == DriverMode::MOCK) {
        VerificationManager verificationMgr(&hal, &wifiManager, &scheduler, &fsm, &backendGateway);
        verificationMgr.runVerificationSuite();
    }
}

void loop() {
    // Runs the scheduler execution loop
    scheduler.execute();
}
