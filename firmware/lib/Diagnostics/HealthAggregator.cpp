#include "HealthAggregator.h"
#include <Arduino.h>

HealthAggregator::HealthAggregator(Scheduler* scheduler, FSM* fsm, WiFiManager* wifi, MQTTManager* mqtt, BackendGateway* backend)
    : _scheduler(scheduler), _fsm(fsm), _wifiManager(wifi), _mqttManager(mqtt), _backendGateway(backend) {}

SubsystemHealth HealthAggregator::aggregateHealth() {
    SubsystemHealth health;
    memset(&health, 0, sizeof(SubsystemHealth));

    if (_scheduler) {
        health.schedulerUtilization = _scheduler->getDiagnostics().getSchedulerUtilization();
    } else {
        health.schedulerUtilization = 0.0f;
    }

    if (_fsm) {
        health.fsmState = static_cast<int>(_fsm->getCurrentState());
    } else {
        health.fsmState = 0;
    }

    if (_wifiManager) {
        health.wifiConnected = _wifiManager->isConnected();
        health.wifiRSSI = _wifiManager->getRSSI();
    } else {
        health.wifiConnected = false;
        health.wifiRSSI = -100;
    }

    if (_mqttManager) {
        health.mqttConnected = _mqttManager->isConnected();
    } else {
        health.mqttConnected = false;
    }

    if (_backendGateway) {
        health.backendSyncState = static_cast<int>(_backendGateway->getSyncState());
    } else {
        health.backendSyncState = 0;
    }

    // Capture dynamic system stats
    health.freeHeap = ESP.getFreeHeap();
    health.batteryLevel = 98.0f; 
    health.sensorsHealthy = (health.fsmState != 5); // Assumes state 5 is Fault state

    return health;
}
