#include "DiagnosticsManager.h"
#include <Arduino.h>
#include <stdio.h>

DiagnosticsManager::DiagnosticsManager(Scheduler* scheduler, FSM* fsm, WiFiManager* wifi, MQTTManager* mqtt, BackendGateway* backend, EventDispatcher* dispatcher) {
    _faultRegistry = new FaultRegistry();
    _faultManager = new FaultManager(_faultRegistry);
    _healthAggregator = new HealthAggregator(scheduler, fsm, wifi, mqtt, backend);
    _watchdogMonitor = new WatchdogMonitor(scheduler, mqtt, backend, _faultManager);
    _eventLogger = new EventLogger();
    _recoveryManager = new RecoveryManager(dispatcher);
    _observerManager = new DiagnosticsObserverManager();

    _lastUpdateTime = 0;
    _updateIntervalMs = 5000; // Perform aggregates every 5s
}

DiagnosticsManager::~DiagnosticsManager() {
    delete _faultRegistry;
    delete _faultManager;
    delete _healthAggregator;
    delete _watchdogMonitor;
    delete _eventLogger;
    delete _recoveryManager;
    delete _observerManager;
}

void DiagnosticsManager::initialize() {
    _eventLogger->logEvent("STATE", "Diagnostics Manager Initialized");
    _recoveryManager->resetRecovery();
}

void DiagnosticsManager::reportFault(int faultId, const char* subsystem, FaultSeverity severity, const char* description) {
    if (!_faultManager) return;
    
    bool alreadyActive = _faultManager->isFaultActive(faultId);
    _faultManager->registerFault(faultId, subsystem, severity, description);
    
    if (!alreadyActive) {
        char buf[80];
        snprintf(buf, sizeof(buf), "[%s] Fault ID %d: %s", subsystem, faultId, description);
        _eventLogger->logEvent("FAULT", buf);
        _observerManager->notifyFaultState(faultId, severity, true, description);
    }
}

void DiagnosticsManager::clearFault(int faultId) {
    if (!_faultManager) return;

    if (_faultManager->isFaultActive(faultId)) {
        _faultManager->clearFault(faultId);
        
        char buf[48];
        snprintf(buf, sizeof(buf), "Cleared fault ID %d", faultId);
        _eventLogger->logEvent("RECOVERY", buf);
        _observerManager->notifyFaultState(faultId, FaultSeverity::INFO, false, "RESOLVED");
        
        // Notify recovery observer
        _observerManager->notifyRecovery(faultId, "RESOLVED");
    }
}

void DiagnosticsManager::feedHeartbeat() {
    if (_watchdogMonitor) {
        _watchdogMonitor->feedHeartbeat();
    }
}

void DiagnosticsManager::feedCommunication() {
    if (_watchdogMonitor) {
        _watchdogMonitor->feedCommunication();
    }
}

void DiagnosticsManager::feedSensorRead() {
    if (_watchdogMonitor) {
        _watchdogMonitor->feedSensorRead();
    }
}

void DiagnosticsManager::update() {
    unsigned long now = millis();
    if (now - _lastUpdateTime < _updateIntervalMs) {
        return;
    }
    _lastUpdateTime = now;

    // 1. Trigger watchdog timer checks
    if (_watchdogMonitor) {
        _watchdogMonitor->performChecks();
    }

    // 2. Aggregate subsystem health
    SubsystemHealth health = _healthAggregator->aggregateHealth();
    if (_observerManager) {
        _observerManager->notifyHealthStatus(health);
    }

    // 3. Process active recovery escalation paths
    FaultSeverity highestActive;
    if (_faultManager && _faultManager->getHighestActiveSeverity(highestActive)) {
        int count = _faultRegistry->getCount();
        FaultRecord rec;
        for (int i = 0; i < count; i++) {
            if (_faultRegistry->getRecord(i, rec)) {
                if (rec.active && rec.severity == highestActive) {
                    // Coordinate recovery escalation step
                    _recoveryManager->handleFault(rec.faultId, rec.severity);
                    _observerManager->notifyRecovery(rec.faultId, _recoveryManager->getRecoveryStatus());
                    
                    char logMsg[64];
                    snprintf(logMsg, sizeof(logMsg), "Escalating recovery for fault %d to: %s", rec.faultId, _recoveryManager->getRecoveryStatus());
                    _eventLogger->logEvent("RECOVERY", logMsg);
                    break; 
                }
            }
        }
    } else {
        if (_recoveryManager) {
            _recoveryManager->resetRecovery();
        }
    }
}
