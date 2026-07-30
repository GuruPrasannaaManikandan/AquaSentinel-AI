#ifndef DIAGNOSTICS_MANAGER_H
#define DIAGNOSTICS_MANAGER_H

#include "HealthAggregator.h"
#include "FaultRegistry.h"
#include "FaultManager.h"
#include "WatchdogMonitor.h"
#include "EventLogger.h"
#include "RecoveryManager.h"
#include "DiagnosticsObserverManager.h"

/**
 * @brief Central class coordinating fault tracking, system health aggregator, software watchdog monitoring, event logging, and recovery.
 */
class DiagnosticsManager {
private:
    FaultRegistry* _faultRegistry;
    FaultManager* _faultManager;
    HealthAggregator* _healthAggregator;
    WatchdogMonitor* _watchdogMonitor;
    EventLogger* _eventLogger;
    RecoveryManager* _recoveryManager;
    DiagnosticsObserverManager* _observerManager;

    unsigned long _lastUpdateTime;
    unsigned long _updateIntervalMs;

public:
    DiagnosticsManager(Scheduler* scheduler, FSM* fsm, WiFiManager* wifi, MQTTManager* mqtt, BackendGateway* backend, EventDispatcher* dispatcher);
    ~DiagnosticsManager();

    void initialize();
    void update();

    /**
     * @brief Manually reports a fault, adding it to the manager, registry, and logger.
     */
    void reportFault(int faultId, const char* subsystem, FaultSeverity severity, const char* description);

    /**
     * @brief Clears an active fault.
     */
    void clearFault(int faultId);

    /**
     * @brief Feeds heartbeat watchdog timer.
     */
    void feedHeartbeat();

    /**
     * @brief Feeds communication watchdog timer.
     */
    void feedCommunication();

    /**
     * @brief Feeds sensor watchdog timer.
     */
    void feedSensorRead();

    // Getters
    FaultRegistry* getRegistry() { return _faultRegistry; }
    FaultManager* getFaultManager() { return _faultManager; }
    HealthAggregator* getHealthAggregator() { return _healthAggregator; }
    WatchdogMonitor* getWatchdogMonitor() { return _watchdogMonitor; }
    EventLogger* getEventLogger() { return _eventLogger; }
    RecoveryManager* getRecoveryManager() { return _recoveryManager; }
    DiagnosticsObserverManager* getObserverManager() { return _observerManager; }
};

#endif // DIAGNOSTICS_MANAGER_H
