#include "MQTTSubscriptionManager.h"
#include <string.h>

MQTTSubscriptionManager::MQTTSubscriptionManager(IMQTTService* service) : _service(service), _subscriptionCount(0) {
    for (int i = 0; i < MQTT_MAX_SUBSCRIPTIONS; i++) {
        _subscriptions[i].active = false;
        _subscriptions[i].topic[0] = '\0';
        _subscriptions[i].handler = nullptr;
    }
}

bool MQTTSubscriptionManager::subscribe(const char* topic, void (*handler)(const char* payload), int qos) {
    if (_subscriptionCount >= MQTT_MAX_SUBSCRIPTIONS) return false;

    // Check duplicate
    for (int i = 0; i < MQTT_MAX_SUBSCRIPTIONS; i++) {
        if (_subscriptions[i].active && strcmp(_subscriptions[i].topic, topic) == 0) {
            _subscriptions[i].handler = handler;
            return true;
        }
    }

    // Find free slot
    for (int i = 0; i < MQTT_MAX_SUBSCRIPTIONS; i++) {
        if (!_subscriptions[i].active) {
            strncpy(_subscriptions[i].topic, topic, 63);
            _subscriptions[i].topic[63] = '\0';
            _subscriptions[i].handler = handler;
            _subscriptions[i].active = true;
            _subscriptionCount++;
            
            if (_service) {
                _service->subscribe(topic, qos);
            }
            return true;
        }
    }
    return false;
}

bool MQTTSubscriptionManager::unsubscribe(const char* topic) {
    for (int i = 0; i < MQTT_MAX_SUBSCRIPTIONS; i++) {
        if (_subscriptions[i].active && strcmp(_subscriptions[i].topic, topic) == 0) {
            _subscriptions[i].active = false;
            _subscriptions[i].topic[0] = '\0';
            _subscriptions[i].handler = nullptr;
            _subscriptionCount--;
            
            if (_service) {
                _service->unsubscribe(topic);
            }
            return true;
        }
    }
    return false;
}

void MQTTSubscriptionManager::dispatchMessage(const char* topic, const char* payload) {
    for (int i = 0; i < MQTT_MAX_SUBSCRIPTIONS; i++) {
        if (_subscriptions[i].active && strcmp(_subscriptions[i].topic, topic) == 0) {
            if (_subscriptions[i].handler) {
                _subscriptions[i].handler(payload);
            }
            break;
        }
    }
}
