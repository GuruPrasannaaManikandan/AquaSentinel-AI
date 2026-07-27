#include "CalibrationValidator.h"
#include "CalibrationProfiles.h"
#include "CalibrationManager.h"
#include "CalibrationMath.h"
#include "repository/MockStorage.h"
#include "repository/CalibrationRepository.h"
#include "repository/RepositoryProfile.h"
#include <Arduino.h>

bool CalibrationValidator::runUnitTests() {
    Serial.println("\n=== STARTING CALIBRATION SELF-VALIDATION TESTS ===");
    bool allPassed = true;

    // Test 1: Freshwater pH Calibration
    FreshwaterProfile fresh;
    CalibrationManager freshMgr(&fresh);
    float phCal = freshMgr.calibrate(SensorType::PH, 2.0f);
    if (phCal == 7.0f) {
        Serial.println("[PASS] Test 1: Freshwater pH 2.0V -> 7.0 pH");
    } else {
        Serial.print("[FAIL] Test 1: expected 7.0, got "); Serial.println(phCal);
        allPassed = false;
    }

    // Test 2: Validation Bands
    ValidationState phState = freshMgr.validate(SensorType::PH, 7.0f);
    if (phState == ValidationState::VALID) {
        Serial.println("[PASS] Test 2: pH 7.0 is VALID");
    } else {
        Serial.println("[FAIL] Test 2");
        allPassed = false;
    }

    // Test 3: Warning Bands
    ValidationState phStateWarn = freshMgr.validate(SensorType::PH, 5.5f);
    if (phStateWarn == ValidationState::WARNING) {
        Serial.println("[PASS] Test 3: pH 5.5 is WARNING");
    } else {
        Serial.println("[FAIL] Test 3");
        allPassed = false;
    }

    // Test 4: Critical Bands
    ValidationState phStateCrit = freshMgr.validate(SensorType::PH, 2.0f);
    if (phStateCrit == ValidationState::CRITICAL) {
        Serial.println("[PASS] Test 4: pH 2.0 is CRITICAL");
    } else {
        Serial.println("[FAIL] Test 4");
        allPassed = false;
    }

    // Test 5: Out-of-Bounds Check
    float rawOutLimit = freshMgr.calibrate(SensorType::PH, 3.5f);
    if (rawOutLimit == -999.0f) {
        Serial.println("[PASS] Test 5: Raw Input 3.5V Out-of-Bounds -> -999.0f");
    } else {
        Serial.print("[FAIL] Test 5: expected -999.0f, got "); Serial.println(rawOutLimit);
        allPassed = false;
    }

    // Test 6: Repository Load/Save Verification
    MockStorage* testStorage = new MockStorage();
    CalibrationRepository testRepo(testStorage);
    
    if (testRepo.initialize()) {
        Serial.println("[PASS] Test 6: Repository initialization loaded valid profile");
    } else {
        Serial.println("[FAIL] Test 6: Repository initialization failed");
        allPassed = false;
    }

    // Test 7: Persistence Recovery Flow
    // Corrupt the storage explicitly
    testStorage->setCorrupted(true);
    
    // Attempting re-initialization should fail validation and fall back to factory backup
    Serial.println("[SYSTEM] Simulating storage corruption test...");
    bool initResult = testRepo.initialize();
    
    if (!initResult) {
        Serial.println("[PASS] Test 7: Repository correctly detected corrupted data and triggered recovery");
    } else {
        Serial.println("[FAIL] Test 7: Repository accepted corrupted data block!");
        allPassed = false;
    }

    Serial.println("=== CALIBRATION SELF-VALIDATION TESTS COMPLETE ===");
    return allPassed;
}
