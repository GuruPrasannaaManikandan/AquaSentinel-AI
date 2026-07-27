#ifndef MQTT_OBSERVER_MANAGER_H
#define MQTT_OBSERVER_MANAGER_H

#include "IMQTTObserver.h"

#define MAX_MQTT_OBSERVERS 5

class MQTTObserverManager {
private:
    IMQTTObserver* _observers[MAX_MQTT_OBSERVERS];
    int _observerCount;

public:
    MQTTObserverManager();
    ~MQTTObserverManager() {}

    bool subscribe(IMQTTObserver* observer);
    bool unsubscribe(IMQTTObserver* observer);
    
    void notifyStateTransition(MQTTState from, MQTTState to);
    void notifyMessagePublished(const char* topic, const char* payload);
    void notifyMessageReceived(const char* topic, const char* payload);
    
    int getObserverCount() const { return _observerCount; }
};

#endif
