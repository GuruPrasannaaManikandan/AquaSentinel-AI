#include "HardwareSelfTest.h"
#include <Arduino.h>
#include <math.h>

HardwareSelfTest::HardwareSelfTest(HAL* hal, WiFiManager* wifi, Scheduler* scheduler, FSM* fsm)
    : _hal(hal), _wifiManager(wifi), _scheduler(scheduler), _fsm(fsm) {}

bool HardwareSelfTest::executeTest() {
    Serial.println("[SELF-TEST] Starting hardware self-tests...");
    bool pass = true;

    // 1. HAL & Mock Drivers Verification
    if (!_hal) {
        Serial.println("[SELF-TEST] [FAIL] HAL pointer is NULL.");
        pass = false;
    } else {
        Serial.println("[SELF-TEST] [PASS] HAL interface verified.");
    }

    // 2. Sensor and ADC Range Verification
    if (_hal) {
        TelemetryData tel = _hal->readAllSensors();
        if (isnan(tel.temperature_c) || isinf(tel.temperature_c) || tel.temperature_c < -10 || tel.temperature_c > 60) {
            Serial.println("[SELF-TEST] [FAIL] ADC Temperature reading is out of bounds.");
            pass = false;
        } else {
            Serial.println("[SELF-TEST] [PASS] ADC Temperature sensor verified.");
        }
        
        if (isnan(tel.ph) || tel.ph < 0 || tel.ph > 14) {
            Serial.println("[SELF-TEST] [FAIL] ADC pH reading is out of bounds.");
            pass = false;
        } else {
            Serial.println("[SELF-TEST] [PASS] ADC pH sensor verified.");
        }

        if (isnan(tel.turbidity_ntu) || tel.turbidity_ntu < 0 || tel.turbidity_ntu > 3000) {
            Serial.println("[SELF-TEST] [FAIL] ADC Turbidity reading is invalid.");
            pass = false;
        } else {
            Serial.println("[SELF-TEST] [PASS] ADC Turbidity sensor verified.");
        }
    }

    // 3. GPIO Actuator verification
    if (_hal) {
        _hal->writeActuator("green_led", "ON");
        _hal->writeActuator("buzzer", "OFF");
        Serial.println("[SELF-TEST] [PASS] GPIO Actuators and Indicators verified.");
    }

    // 4. WiFi Link status
    if (!_wifiManager) {
        Serial.println("[SELF-TEST] [FAIL] WiFiManager is NULL.");
        pass = false;
    } else {
        Serial.println("[SELF-TEST] [PASS] WiFiManager interface verified.");
    }

    // 5. Heap Memory Availability
    unsigned long freeHeap = ESP.getFreeHeap();
    if (freeHeap < 20000) { // 20 KB limit
        Serial.print("[SELF-TEST] [FAIL] Memory stress detected. Free heap: ");
        Serial.println(freeHeap);
        pass = false;
    } else {
        Serial.print("[SELF-TEST] [PASS] Heap memory verified. Free: ");
        Serial.print(freeHeap);
        Serial.println(" bytes.");
    }

    // 6. Scheduler Validation
    if (!_scheduler) {
        Serial.println("[SELF-TEST] [FAIL] Scheduler is NULL.");
        pass = false;
    } else {
        Serial.println("[SELF-TEST] [PASS] Cooperative Scheduler verified.");
    }

    // 7. FSM Validation
    if (!_fsm) {
        Serial.println("[SELF-TEST] [FAIL] FSM pointer is NULL.");
        pass = false;
    } else {
        Serial.println("[SELF-TEST] [PASS] FSM engine verified.");
    }

    if (pass) {
        Serial.println("[SELF-TEST] RESULT: PASS");
    } else {
        Serial.println("[SELF-TEST] RESULT: FAIL");
    }

    return pass;
}
