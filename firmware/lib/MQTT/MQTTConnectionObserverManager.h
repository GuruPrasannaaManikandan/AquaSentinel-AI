#ifndef MQTT_CONNECTION_OBSERVER_MANAGER_H
#define MQTT_CONNECTION_OBSERVER_MANAGER_H

#include "IMQTTConnectionObserver.h"

#define MAX_MQTT_CONN_OBSERVERS 5

class MQTTConnectionObserverManager {
private:
    IMQTTConnectionObserver* _observers[MAX_MQTT_CONN_OBSERVERS];
    int _observerCount;

public:
    MQTTConnectionObserverManager();
    ~MQTTConnectionObserverManager() {}

    bool subscribe(IMQTTConnectionObserver* observer);
    bool unsubscribe(IMQTTConnectionObserver* observer);
    
    void notifyConnected();
    void notifyDisconnected();
    void notifyBrokerLost();
    void notifyReconnect();
    void notifyAuthenticationFailure();
    
    int getObserverCount() const { return _observerCount; }
};

#endif
