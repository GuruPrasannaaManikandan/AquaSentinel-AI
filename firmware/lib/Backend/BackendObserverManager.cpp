#include "BackendObserverManager.h"
#include <string.h>

BackendObserverManager::BackendObserverManager() : _count(0) {
    memset(_observers, 0, sizeof(_observers));
}

bool BackendObserverManager::subscribe(IBackendObserver* observer) {
    if (!observer || _count >= MAX_BACKEND_OBSERVERS) {
        return false;
    }
    
    // Avoid duplicates
    for (int i = 0; i < _count; i++) {
        if (_observers[i] == observer) {
            return true;
        }
    }
    
    _observers[_count++] = observer;
    return true;
}

bool BackendObserverManager::unsubscribe(IBackendObserver* observer) {
    if (!observer) return false;
    
    for (int i = 0; i < _count; i++) {
        if (_observers[i] == observer) {
            // Shift remaining elements
            for (int j = i; j < _count - 1; j++) {
                _observers[j] = _observers[j + 1];
            }
            _observers[--_count] = nullptr;
            return true;
        }
    }
    return false;
}

void BackendObserverManager::notifySyncStateTransition(BackendSyncState fromState, BackendSyncState toState) {
    for (int i = 0; i < _count; i++) {
        if (_observers[i]) {
            _observers[i]->onSyncStateTransition(fromState, toState);
        }
    }
}

void BackendObserverManager::notifyConfigUpdated(const char* version, unsigned long telemetryIntervalMs) {
    for (int i = 0; i < _count; i++) {
        if (_observers[i]) {
            _observers[i]->onConfigUpdated(version, telemetryIntervalMs);
        }
    }
}

void BackendObserverManager::notifyTelemetryBuffered(const TelemetryData& data, int currentCount) {
    for (int i = 0; i < _count; i++) {
        if (_observers[i]) {
            _observers[i]->onTelemetryBuffered(data, currentCount);
        }
    }
}

void BackendObserverManager::notifyTelemetryDropped(const TelemetryData& droppedData) {
    for (int i = 0; i < _count; i++) {
        if (_observers[i]) {
            _observers[i]->onTelemetryDropped(droppedData);
        }
    }
}

void BackendObserverManager::notifyDiagnosticsSynced() {
    for (int i = 0; i < _count; i++) {
        if (_observers[i]) {
            _observers[i]->onDiagnosticsSynced();
        }
    }
}
