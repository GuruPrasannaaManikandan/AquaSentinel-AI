#ifndef SYSTEM_TEST_RUNNER_H
#define SYSTEM_TEST_RUNNER_H

#include "hal/HAL.h"
#include "FSM.h"
#include "BackendGateway.h"

/**
 * @brief Class executing automated integration scenarios (WiFi drop, reconnect, queue flushes, sensor bounds).
 */
class SystemTestRunner {
private:
    HAL* _hal;
    FSM* _fsm;
    BackendGateway* _backendGateway;

public:
    SystemTestRunner(HAL* hal, FSM* fsm, BackendGateway* backend);
    ~SystemTestRunner() {}

    /**
     * @brief Runs scenario steps. Returns true if PASS, false if FAIL.
     */
    bool runAutomatedScenarios();
};

#endif // SYSTEM_TEST_RUNNER_H
