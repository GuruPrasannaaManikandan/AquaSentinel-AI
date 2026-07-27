#ifndef WIFI_OBSERVER_MANAGER_H
#define WIFI_OBSERVER_MANAGER_H

#include "IWiFiObserver.h"

#define MAX_WIFI_OBSERVERS 5

class WiFiObserverManager {
private:
    IWiFiObserver* _observers[MAX_WIFI_OBSERVERS];
    int _observerCount;

public:
    WiFiObserverManager();
    ~WiFiObserverManager() {}

    bool subscribe(IWiFiObserver* observer);
    bool unsubscribe(IWiFiObserver* observer);
    
    void notifyStateTransition(WiFiState from, WiFiState to);
    void notifySignalChanged(int rssi);
    
    int getObserverCount() const { return _observerCount; }
};

#endif
