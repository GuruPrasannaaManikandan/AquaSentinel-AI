#ifndef IMQTT_CONNECTION_OBSERVER_H
#define IMQTT_CONNECTION_OBSERVER_H

#include "MQTTState.h"

/**
 * @brief Observer callback interface tracking connection lifecycle changes.
 */
class IMQTTConnectionObserver {
public:
    virtual ~IMQTTConnectionObserver() {}

    virtual void onConnected() = 0;
    virtual void onDisconnected() = 0;
    virtual void onBrokerLost() = 0;
    virtual void onReconnect() = 0;
    virtual void onAuthenticationFailure() = 0;
};

#endif
