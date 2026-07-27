#include "MQTTObserverManager.h"
#include <Arduino.h>

MQTTObserverManager::MQTTObserverManager() : _observerCount(0) {
    for (int i = 0; i < MAX_MQTT_OBSERVERS; i++) {
        _observers[i] = nullptr;
    }
}

bool MQTTObserverManager::subscribe(IMQTTObserver* observer) {
    if (!observer || _observerCount >= MAX_MQTT_OBSERVERS) return false;

    // Check duplicate
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i] == observer) {
            return false;
        }
    }

    _observers[_observerCount++] = observer;
    return true;
}

bool MQTTObserverManager::unsubscribe(IMQTTObserver* observer) {
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

void MQTTObserverManager::notifyStateTransition(MQTTState from, MQTTState to) {
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i]) {
            _observers[i]->onMQTTStateTransition(from, to);
        }
    }
}

void MQTTObserverManager::notifyMessagePublished(const char* topic, const char* payload) {
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i]) {
            _observers[i]->onMessagePublished(topic, payload);
        }
    }
}

void MQTTObserverManager::notifyMessageReceived(const char* topic, const char* payload) {
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i]) {
            _observers[i]->onMessageReceived(topic, payload);
        }
    }
}
