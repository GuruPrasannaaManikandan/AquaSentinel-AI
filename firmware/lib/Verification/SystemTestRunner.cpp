#include "SystemTestRunner.h"
#include "MockWiFiService.h"
#include "MockMQTTService.h"
#include <Arduino.h>

extern MockWiFiService mockWiFi;
extern MockMQTTService mockMQTT;

SystemTestRunner::SystemTestRunner(HAL* hal, FSM* fsm, BackendGateway* backend)
    : _hal(hal), _fsm(fsm), _backendGateway(backend) {}

bool SystemTestRunner::runAutomatedScenarios() {
    Serial.println("[TEST-RUNNER] Starting automated system verification...");
    bool pass = true;

    WiFiState initialWiFiState = mockWiFi.getStatus();
    MQTTState initialMQTTState = mockMQTT.getStatus();

    // 1. Scenario: Normal Operation
    Serial.println("[TEST-RUNNER] Scenario 1: Normal Operation Check");
    if (_backendGateway) {
        TelemetryData data = _hal ? _hal->readAllSensors() : TelemetryData{25.0f, 7.2f, 8.5f, 15.0f, 35.0f};
        _backendGateway->publishTelemetry(data);
        Serial.println("[TEST-RUNNER] [PASS] Normal Telemetry processing executed.");
    } else {
        Serial.println("[TEST-RUNNER] [FAIL] BackendGateway is not available.");
        pass = false;
    }

    // 2. Scenario: WiFi Connection Loss
    Serial.println("[TEST-RUNNER] Scenario 2: Wi-Fi Disconnection and Telemetry Buffering");
    if (_backendGateway && _backendGateway->getOfflineBuffer()) {
        mockWiFi.setStatus(WiFiState::DISCONNECTED);
        _backendGateway->setWiFiConnected(false);
        _backendGateway->update();

        if (_backendGateway->getSyncState() != BackendSyncState::RECOVERING) {
            Serial.println("[TEST-RUNNER] [FAIL] Gateway did not transition to RECOVERING after Wi-Fi loss.");
            pass = false;
        } else {
            Serial.println("[TEST-RUNNER] [PASS] Gateway transitioned to RECOVERING.");
        }

        int initialCount = _backendGateway->getOfflineBuffer()->getCount();
        TelemetryData data = {26.0f, 7.3f, 8.4f, 16.0f, 34.5f};
        _backendGateway->publishTelemetry(data);

        if (_backendGateway->getOfflineBuffer()->getCount() != initialCount + 1) {
            Serial.println("[TEST-RUNNER] [FAIL] Telemetry was not buffered in offline mode.");
            pass = false;
        } else {
            Serial.println("[TEST-RUNNER] [PASS] Telemetry enqueued in Offline Buffer successfully.");
        }
    } else {
        pass = false;
    }

    // 3. Scenario: MQTT Broker Outage
    Serial.println("[TEST-RUNNER] Scenario 3: MQTT Disconnection Check");
    if (_backendGateway) {
        mockMQTT.disconnect();
        _backendGateway->update();
        if (_backendGateway->getSyncState() != BackendSyncState::RECOVERING) {
            Serial.println("[TEST-RUNNER] [FAIL] Gateway did not maintain RECOVERING/FAILED state on MQTT loss.");
            pass = false;
        } else {
            Serial.println("[TEST-RUNNER] [PASS] MQTT Outage handling verified.");
        }
    }

    // 4. Scenario: Backend Recovery and Buffer Flush
    Serial.println("[TEST-RUNNER] Scenario 4: Connection Recovery and Buffer Flushing");
    if (_backendGateway && _backendGateway->getOfflineBuffer()) {
        mockWiFi.setStatus(WiFiState::CONNECTED);
        _backendGateway->setWiFiConnected(true);
        
        mockMQTT.connect(MQTTConfig{}); 
        _backendGateway->update();
        _backendGateway->update();

        if (_backendGateway->getOfflineBuffer()->getCount() != 0) {
            Serial.print("[TEST-RUNNER] [FAIL] Buffer not flushed. Remaining items: ");
            Serial.println(_backendGateway->getOfflineBuffer()->getCount());
            pass = false;
        } else {
            Serial.println("[TEST-RUNNER] [PASS] Buffer flushed on recovery.");
        }
    }

    // Restore initial mock states
    mockWiFi.setStatus(initialWiFiState);
    if (initialMQTTState == MQTTState::CONNECTED) {
        mockMQTT.connect(MQTTConfig{});
    } else {
        mockMQTT.disconnect();
    }
    _backendGateway->setWiFiConnected(initialWiFiState == WiFiState::CONNECTED);

    if (pass) {
        Serial.println("[TEST-RUNNER] RESULT: ALL INTEGRATION SCENARIOS PASS");
    } else {
        Serial.println("[TEST-RUNNER] RESULT: SCENARIOS FAIL");
    }

    return pass;
}
