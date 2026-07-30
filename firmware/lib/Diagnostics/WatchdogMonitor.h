#ifndef WATCHDOG_MONITOR_H
#define WATCHDOG_MONITOR_H

#include "Scheduler.h"
#include "MQTTManager.h"
#include "BackendGateway.h"
#include "FaultManager.h"

/**
 * @brief Monitor tracking timing violations, task overruns, and comm/sensor timeouts.
 */
class WatchdogMonitor {
private:
    Scheduler* _scheduler;
    MQTTManager* _mqttManager;
    BackendGateway* _backendGateway;
    FaultManager* _faultManager;

    unsigned long _lastHeartbeatSuccessTime;
    unsigned long _lastCommSuccessTime;
    unsigned long _lastSensorReadTime;

    unsigned long _heartbeatTimeoutLimitMs;
    unsigned long _commTimeoutLimitMs;
    unsigned long _sensorTimeoutLimitMs;
    unsigned long _longestTaskExecutionThresholdUs;

public:
    WatchdogMonitor(Scheduler* scheduler, MQTTManager* mqtt, BackendGateway* backend, FaultManager* faultMgr);
    ~WatchdogMonitor() {}

    /**
     * @brief Feeds the heartbeat watchdog timer.
     */
    void feedHeartbeat();

    /**
     * @brief Feeds the communication watchdog timer.
     */
    void feedCommunication();

    /**
     * @brief Feeds the sensor watchdog timer.
     */
    void feedSensorRead();

    /**
     * @brief Performs tick checks against all timeouts and overrun thresholds.
     */
    void performChecks();
};

#endif // WATCHDOG_MONITOR_H
