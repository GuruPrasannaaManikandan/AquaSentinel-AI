#ifndef MQTT_SUBSCRIPTION_MANAGER_H
#define MQTT_SUBSCRIPTION_MANAGER_H

#include "IMQTTService.h"

#define MQTT_MAX_SUBSCRIPTIONS 4

struct MQTTSubscription {
    char topic[64];
    void (*handler)(const char* payload);
    bool active;
};

/**
 * @brief Manages topics subscriptions and maps callbacks to incoming payloads.
 */
class MQTTSubscriptionManager {
private:
    IMQTTService* _service;
    MQTTSubscription _subscriptions[MQTT_MAX_SUBSCRIPTIONS];
    int _subscriptionCount;

public:
    MQTTSubscriptionManager(IMQTTService* service);
    ~MQTTSubscriptionManager() {}

    bool subscribe(const char* topic, void (*handler)(const char* payload), int qos = 0);
    bool unsubscribe(const char* topic);
    void dispatchMessage(const char* topic, const char* payload);
};

#endif
