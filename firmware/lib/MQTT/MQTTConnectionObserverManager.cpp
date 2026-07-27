#include "MQTTConnectionObserverManager.h"
#include <Arduino.h>

MQTTConnectionObserverManager::MQTTConnectionObserverManager() : _observerCount(0) {
    for (int i = 0; i < MAX_MQTT_CONN_OBSERVERS; i++) {
        _observers[i] = nullptr;
    }
}

bool MQTTConnectionObserverManager::subscribe(IMQTTConnectionObserver* observer) {
    if (!observer || _observerCount >= MAX_MQTT_CONN_OBSERVERS) return false;

    // Check duplicate
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i] == observer) {
            return false;
        }
    }

    _observers[_observerCount++] = observer;
    return true;
}

bool MQTTConnectionObserverManager::unsubscribe(IMQTTConnectionObserver* observer) {
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

void MQTTConnectionObserverManager::notifyConnected() {
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i]) _observers[i]->onConnected();
    }
}

void MQTTConnectionObserverManager::notifyDisconnected() {
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i]) _observers[i]->onDisconnected();
    }
}

void MQTTConnectionObserverManager::notifyBrokerLost() {
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i]) _observers[i]->onBrokerLost();
    }
}

void MQTTConnectionObserverManager::notifyReconnect() {
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i]) _observers[i]->onReconnect();
    }
}

void MQTTConnectionObserverManager::notifyAuthenticationFailure() {
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i]) _observers[i]->onAuthenticationFailure();
    }
}
