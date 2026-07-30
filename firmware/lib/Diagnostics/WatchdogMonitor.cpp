#include "WatchdogMonitor.h"
#include <Arduino.h>
#include <stdio.h>

WatchdogMonitor::WatchdogMonitor(Scheduler* scheduler, MQTTManager* mqtt, BackendGateway* backend, FaultManager* faultMgr)
    : _scheduler(scheduler), _mqttManager(mqtt), _backendGateway(backend), _faultManager(faultMgr) {
    
    unsigned long now = millis();
    _lastHeartbeatSuccessTime = now;
    _lastCommSuccessTime = now;
    _lastSensorReadTime = now;

    // Production watchdog thresholds
    _heartbeatTimeoutLimitMs = 30000;              // 30s
    _commTimeoutLimitMs = 60000;                   // 60s
    _sensorTimeoutLimitMs = 15000;                 // 15s
    _longestTaskExecutionThresholdUs = 100000;     // 100ms
}

void WatchdogMonitor::feedHeartbeat() {
    _lastHeartbeatSuccessTime = millis();
    if (_faultManager && _faultManager->isFaultActive(10)) {
        _faultManager->clearFault(10);
    }
}

void WatchdogMonitor::feedCommunication() {
    _lastCommSuccessTime = millis();
    if (_faultManager && _faultManager->isFaultActive(11)) {
        _faultManager->clearFault(11);
    }
}

void WatchdogMonitor::feedSensorRead() {
    _lastSensorReadTime = millis();
    if (_faultManager && _faultManager->isFaultActive(12)) {
        _faultManager->clearFault(12);
    }
}

void WatchdogMonitor::performChecks() {
    if (!_faultManager) return;

    unsigned long now = millis();

    // 1. Heartbeat timeout check
    if (now - _lastHeartbeatSuccessTime > _heartbeatTimeoutLimitMs) {
        _faultManager->registerFault(10, "BACKEND", FaultSeverity::WARNING, "Heartbeat Timeout (No tick received)");
    }

    // 2. Communication timeout check
    if (now - _lastCommSuccessTime > _commTimeoutLimitMs) {
        _faultManager->registerFault(11, "MQTT", FaultSeverity::ERROR, "Communication Timeout (Link lost)");
    }

    // 3. Sensor timeout check
    if (now - _lastSensorReadTime > _sensorTimeoutLimitMs) {
        _faultManager->registerFault(12, "SENSORS", FaultSeverity::ERROR, "Sensor Polling Timeout (Reads frozen)");
    }

    // 4. Task execution overrun check
    if (_scheduler) {
        unsigned long longestUs = _scheduler->getDiagnostics().getLongestExecutionUs();
        if (longestUs > _longestTaskExecutionThresholdUs) {
            char desc[64];
            snprintf(desc, sizeof(desc), "Task execution exceeded threshold: %lu us", longestUs);
            _faultManager->registerFault(13, "SCHEDULER", FaultSeverity::WARNING, desc);
        } else if (_faultManager->isFaultActive(13)) {
            _faultManager->clearFault(13);
        }

        // High CPU utilization check
        float utilization = _scheduler->getDiagnostics().getSchedulerUtilization();
        if (utilization > 95.0f) {
            _faultManager->registerFault(14, "SCHEDULER", FaultSeverity::WARNING, "CPU utilization exceeds 95%");
        } else if (_faultManager->isFaultActive(14)) {
            _faultManager->clearFault(14);
        }
    }
}
