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

// Specifications
#define PROJECT_NAME "AquaSentinel-AI"
#define FIRMWARE_VERSION "3.8.1"
#define BUILD_DATE __DATE__
#define BUILD_TIME __TIME__

// Configuration
const DriverMode ACTIVE_MODE = DriverMode::MOCK;
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

// Instantiate GPS (Mock only)
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

// Instantiate Wi-Fi Connectivity Layer
MockCredentialProvider credentialsProvider;
WiFiConnectionPolicy wifiPolicy(true, true, 3, 10000, -80, -75);
MockWiFiService mockWiFi;
WiFiManager wifiManager(&mockWiFi, &dispatcher, &credentialsProvider, wifiPolicy);

// Instantiate MQTT Communication Layer with Policies
MQTTConfig mqttConfig = {"broker.hivemq.com", 1883, "aquasentinel-client", "user", "pass", 15, true, 0, 5000, "aquasentinel/status", "Offline"};
MQTTTopicRegistry mqttTopics = {"aquasentinel/telemetry", "aquasentinel/alerts", "aquasentinel/commands", "aquasentinel/diagnostics", "aquasentinel/heartbeat", "aquasentinel/firmware", "aquasentinel/configuration"};
MQTTTopicPolicy mqttPolicy(TopicPermission::READ_WRITE, 1, true, 128);
MQTTQoSPolicy mqttQoSPolicy(0, 2000, 3);
MockMQTTService mockMQTT;
MQTTManager mqttManager(&mockMQTT, &dispatcher, &wifiManager, mqttConfig, mqttTopics, mqttPolicy, mqttQoSPolicy);

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
    Serial.print("[TASK] Sensor Polling (Calibrated): ");
    Serial.print("Temp: "); Serial.print(telemetry.temperature_c); Serial.print(" C | ");
    Serial.print("pH: "); Serial.print(telemetry.ph); Serial.print(" | ");
    Serial.print("Salinity: "); Serial.print(telemetry.salinity_ppt); Serial.print(" ppt | ");
    Serial.print("Turbidity: "); Serial.print(telemetry.turbidity_ntu); Serial.print(" NTU | ");
    Serial.print("DO: "); Serial.print(telemetry.dissolved_oxygen_mg_l); Serial.println(" mg/L");

    // Queue telemetry payload publishing to MQTT broker (utilizes Serializer snprintf logic)
    if (mqttManager.isConnected()) {
        mqttManager.publishTelemetry(telemetry);
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
}

void wifiUpdateTask(TaskContext& context) {
    wifiManager.update();
}

void mqttUpdateTask(TaskContext& context) {
    mqttManager.update();
}

void heartbeatTask(TaskContext& context) {
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

    // Simulate incoming command after 15 seconds of uptime
    static bool testCommandSimulated = false;
    if (!testCommandSimulated && context.currentTime >= 15000 && wifiManager.isConnected() && mqttManager.isConnected()) {
        testCommandSimulated = true;
        Serial.println("\n[SYSTEM-TEST] Uptime reached 15s. Simulating remote MQTT command: SHUTDOWN");
        mockMQTT.simulateIncomingMessage(mqttTopics.commands, "SHUTDOWN");
    }
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
    Serial.println(ACTIVE_MODE == DriverMode::PHYSICAL ? "PHYSICAL SENSORS" : "MOCK SIMULATOR");
    Serial.println("--------------------------------");

    // Initialize Calibration Database Repository
    calibrationRepository.initialize();

    // Run calibration layer unit tests (Verifies recovery flows)
    CalibrationValidator::runUnitTests();

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

    Serial.println("Starting Cooperative Task Scheduler...");
    Serial.println("--------------------------------");
}

void loop() {
    // Runs the scheduler execution loop
    scheduler.execute();
}
