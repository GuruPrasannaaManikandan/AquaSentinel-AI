#ifndef IMQTT_OBSERVER_H
#define IMQTT_OBSERVER_H

#include "MQTTState.h"

/**
 * @brief Observer callback interface tracking connection events.
 */
class IMQTTObserver {
public:
    virtual ~IMQTTObserver() {}

    virtual void onMQTTStateTransition(MQTTState fromState, MQTTState toState) = 0;
    virtual void onMessagePublished(const char* topic, const char* payload) = 0;
    virtual void onMessageReceived(const char* topic, const char* payload) = 0;
};

#endif
