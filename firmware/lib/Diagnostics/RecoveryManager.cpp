#include "RecoveryManager.h"
#include <Arduino.h>
#include <stdio.h>

#ifdef HIGH
#undef HIGH
#endif

RecoveryManager::RecoveryManager(EventDispatcher* dispatcher)
    : _dispatcher(dispatcher), _escalationLevel(RecoveryEscalationLevel::RETRY), _retryCount(0), _maxRetries(3) {
    strcpy(_status, "IDLE");
}

void RecoveryManager::resetRecovery() {
    _escalationLevel = RecoveryEscalationLevel::RETRY;
    _retryCount = 0;
    strcpy(_status, "IDLE");
}

void RecoveryManager::handleFault(int faultId, FaultSeverity severity) {
    if (!_dispatcher) return;

    Serial.print("[RECOVERY-MANAGER] Evaluating recovery for Fault ID: ");
    Serial.print(faultId);
    Serial.print(" | Severity: ");
    Serial.println(getFaultSeverityName(severity));

    if (severity == FaultSeverity::INFO) {
        strcpy(_status, "INFO_ONLY");
        return;
    }

    if (severity == FaultSeverity::WARNING) {
        if (_escalationLevel == RecoveryEscalationLevel::RETRY) {
            _retryCount++;
            snprintf(_status, sizeof(_status), "RETRY_%u_OF_%u", _retryCount, _maxRetries);
            if (_retryCount >= _maxRetries) {
                _escalationLevel = RecoveryEscalationLevel::RESTART;
            }
        } else if (_escalationLevel == RecoveryEscalationLevel::RESTART) {
            strcpy(_status, "RESTART_PENDING");
            _dispatcher->publish(Event::WARNING_DETECTED, EventSource::SYSTEM, EventPriority::HIGH, nullptr);
        }
        return;
    }

    if (severity == FaultSeverity::ERROR) {
        if (_escalationLevel != RecoveryEscalationLevel::SHUTDOWN) {
            strcpy(_status, "RESTART_SUB");
            _dispatcher->publish(Event::FAULT_DETECTED, EventSource::SYSTEM, EventPriority::HIGH, nullptr);
            _escalationLevel = RecoveryEscalationLevel::SHUTDOWN;
        } else {
            strcpy(_status, "ESCALATING");
            _dispatcher->publish(Event::SHUTDOWN_REQUEST, EventSource::SYSTEM, EventPriority::CRITICAL, nullptr);
        }
        return;
    }

    if (severity == FaultSeverity::CRITICAL) {
        strcpy(_status, "SHUTTING_DOWN");
        _dispatcher->publish(Event::SHUTDOWN_REQUEST, EventSource::SYSTEM, EventPriority::CRITICAL, nullptr);
        return;
    }
}
