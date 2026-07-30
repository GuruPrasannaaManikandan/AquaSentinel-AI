#ifndef HARDWARE_SELF_TEST_H
#define HARDWARE_SELF_TEST_H

#include "hal/HAL.h"
#include "WiFiManager.h"
#include "Scheduler.h"
#include "FSM.h"

/**
 * @brief Class executing hardware-level self-tests on HAL, drivers, network, memory, and RTOS FSM.
 */
class HardwareSelfTest {
private:
    HAL* _hal;
    WiFiManager* _wifiManager;
    Scheduler* _scheduler;
    FSM* _fsm;

public:
    HardwareSelfTest(HAL* hal, WiFiManager* wifi, Scheduler* scheduler, FSM* fsm);
    ~HardwareSelfTest() {}

    /**
     * @brief Executes tests. Returns true if PASS, false if FAIL.
     */
    bool executeTest();
};

#endif // HARDWARE_SELF_TEST_H
