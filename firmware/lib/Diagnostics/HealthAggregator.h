#ifndef HEALTH_AGGREGATOR_H
#define HEALTH_AGGREGATOR_H

#include "Scheduler.h"
#include "FSM.h"
#include "WiFiManager.h"
#include "MQTTManager.h"
#include "BackendGateway.h"

/**
 * @brief Struct holding aggregated health metrics across all firmware modules.
 */
struct SubsystemHealth {
    float schedulerUtilization;
    int fsmState;
    bool wifiConnected;
    int wifiRSSI;
    bool mqttConnected;
    int backendSyncState;
    unsigned long freeHeap;
    float batteryLevel;
    bool sensorsHealthy;
};

/**
 * @brief Aggregator collecting health data from all active subsystems.
 */
class HealthAggregator {
private:
    Scheduler* _scheduler;
    FSM* _fsm;
    WiFiManager* _wifiManager;
    MQTTManager* _mqttManager;
    BackendGateway* _backendGateway;

public:
    HealthAggregator(Scheduler* scheduler, FSM* fsm, WiFiManager* wifi, MQTTManager* mqtt, BackendGateway* backend);
    ~HealthAggregator() {}

    /**
     * @brief Compiles current health snapshots from all registered pointers.
     */
    SubsystemHealth aggregateHealth();
};

#endif // HEALTH_AGGREGATOR_H
