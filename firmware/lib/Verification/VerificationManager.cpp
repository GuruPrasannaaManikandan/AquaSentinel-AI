#include "VerificationManager.h"
#include <Arduino.h>

VerificationManager::VerificationManager(HAL* hal, WiFiManager* wifi, Scheduler* scheduler, FSM* fsm, BackendGateway* backend) {
    _selfTest = new HardwareSelfTest(hal, wifi, scheduler, fsm);
    _testRunner = new SystemTestRunner(hal, fsm, backend);
    _selfTestPassed = false;
    _integrationPassed = false;
}

VerificationManager::~VerificationManager() {
    delete _selfTest;
    delete _testRunner;
}

void VerificationManager::runVerificationSuite() {
    Serial.println("==========================================================");
    Serial.println("         AQUASENTINEL-AI E2E VERIFICATION SUITE           ");
    Serial.println("==========================================================");

    if (_selfTest) {
        _selfTestPassed = _selfTest->executeTest();
    } else {
        _selfTestPassed = false;
    }

    Serial.println("----------------------------------------------------------");

    if (_testRunner) {
        _integrationPassed = _testRunner->runAutomatedScenarios();
    } else {
        _integrationPassed = false;
    }

    Serial.println("==========================================================");
    Serial.println("                  VERIFICATION SUMMARY                    ");
    Serial.println("==========================================================");
    
    Serial.print("Hardware Self-Tests:        ");
    Serial.println(_selfTestPassed ? "PASS" : "FAIL");

    Serial.print("System Integration Tests:   ");
    Serial.println(_integrationPassed ? "PASS" : "FAIL");

    Serial.println("----------------------------------------------------------");
    
    if (_selfTestPassed && _integrationPassed) {
        Serial.println("OVERALL STATUS: SUCCESS / PASS");
    } else {
        Serial.println("OVERALL STATUS: FAILURE / FAIL");
    }
    Serial.println("==========================================================");
}
