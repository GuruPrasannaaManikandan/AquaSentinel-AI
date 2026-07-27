#include "WiFiObserverManager.h"
#include <Arduino.h>

WiFiObserverManager::WiFiObserverManager() : _observerCount(0) {
    for (int i = 0; i < MAX_WIFI_OBSERVERS; i++) {
        _observers[i] = nullptr;
    }
}

bool WiFiObserverManager::subscribe(IWiFiObserver* observer) {
    if (!observer || _observerCount >= MAX_WIFI_OBSERVERS) return false;

    // Check duplicate
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i] == observer) {
            return false;
        }
    }

    _observers[_observerCount++] = observer;
    return true;
}

bool WiFiObserverManager::unsubscribe(IWiFiObserver* observer) {
    int targetIndex = -1;
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i] == observer) {
            targetIndex = i;
            break;
        }
    }

    if (targetIndex == -1) return false;

    for (int i = targetIndex; i < _observerCount - 1; i++) {
        _observers[i] = _observers[i + 1];
    }
    _observers[--_observerCount] = nullptr;
    return true;
}

void WiFiObserverManager::notifyStateTransition(WiFiState from, WiFiState to) {
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i]) {
            _observers[i]->onWiFiStateTransition(from, to);
        }
    }
}

void WiFiObserverManager::notifySignalChanged(int rssi) {
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i]) {
            _observers[i]->onSignalChanged(rssi);
        }
    }
}
