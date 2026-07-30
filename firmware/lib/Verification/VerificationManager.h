#ifndef VERIFICATION_MANAGER_H
#define VERIFICATION_MANAGER_H

#include "HardwareSelfTest.h"
#include "SystemTestRunner.h"
#include "hal/HAL.h"
#include "WiFiManager.h"
#include "Scheduler.h"
#include "FSM.h"
#include "BackendGateway.h"

/**
 * @brief Subsystem Verification Manager orchestrating self-tests and integration test execution.
 */
class VerificationManager {
private:
    HardwareSelfTest* _selfTest;
    SystemTestRunner* _testRunner;

    bool _selfTestPassed;
    bool _integrationPassed;

public:
    VerificationManager(HAL* hal, WiFiManager* wifi, Scheduler* scheduler, FSM* fsm, BackendGateway* backend);
    ~VerificationManager();

    /**
     * @brief Triggers the test suites and reports outcome summary.
     */
    void runVerificationSuite();

    bool isPassed() const { return _selfTestPassed && _integrationPassed; }
};

#endif // VERIFICATION_MANAGER_H
