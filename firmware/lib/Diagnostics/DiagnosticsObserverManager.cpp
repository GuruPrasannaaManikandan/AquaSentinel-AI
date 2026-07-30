#include "DiagnosticsObserverManager.h"
#include <string.h>

DiagnosticsObserverManager::DiagnosticsObserverManager() : _count(0) {
    memset(_observers, 0, sizeof(_observers));
}

bool DiagnosticsObserverManager::subscribe(IDiagnosticsObserver* observer) {
    if (!observer || _count >= MAX_DIAGNOSTICS_OBSERVERS) {
        return false;
    }
    for (int i = 0; i < _count; i++) {
        if (_observers[i] == observer) {
            return true;
        }
    }
    _observers[_count++] = observer;
    return true;
}

bool DiagnosticsObserverManager::unsubscribe(IDiagnosticsObserver* observer) {
    if (!observer) return false;
    for (int i = 0; i < _count; i++) {
        if (_observers[i] == observer) {
            for (int j = i; j < _count - 1; j++) {
                _observers[j] = _observers[j + 1];
            }
            _observers[--_count] = nullptr;
            return true;
        }
    }
    return false;
}

void DiagnosticsObserverManager::notifyHealthStatus(const SubsystemHealth& health) {
    for (int i = 0; i < _count; i++) {
        if (_observers[i]) {
            _observers[i]->onHealthStatusAggregated(health);
        }
    }
}

void DiagnosticsObserverManager::notifyFaultState(int faultId, FaultSeverity severity, bool active, const char* description) {
    for (int i = 0; i < _count; i++) {
        if (_observers[i]) {
            _observers[i]->onFaultStateChanged(faultId, severity, active, description);
        }
    }
}

void DiagnosticsObserverManager::notifyRecovery(int faultId, const char* status) {
    for (int i = 0; i < _count; i++) {
        if (_observers[i]) {
            _observers[i]->onRecoveryExecuted(faultId, status);
        }
    }
}
