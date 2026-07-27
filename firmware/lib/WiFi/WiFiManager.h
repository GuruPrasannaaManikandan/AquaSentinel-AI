#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include "IWiFiService.h"
#include "WiFiConnectionPolicy.h"
#include "ICredentialsProvider.h"
#include "WiFiRetryManager.h"
#include "WiFiDiagnostics.h"
#include "EventDispatcher.h"
#include "WiFiObserverManager.h"
#include "WiFiConnectionHistory.h"

class WiFiManager {
private:
    IWiFiService* _service;
    EventDispatcher* _dispatcher;
    ICredentialsProvider* _credentials;
    WiFiConnectionPolicy _policy;
    
    WiFiRetryManager _retryManager;
    WiFiDiagnostics _diagnostics;
    WiFiObserverManager _observerManager;
    WiFiConnectionHistory _history;

    WiFiState _currentState;
    unsigned long _connectingTimeStart;
    unsigned long _sessionStartTimeMs;
    unsigned long _totalConnects;
    unsigned long _totalConnectTimeMs;
    unsigned long _totalConnectionDurationMs;

    // Transition Guards
    bool guardSSIDFound();
    bool guardAuthSuccess();
    bool guardIPAcquired();

    // Transition Actions
    void actionOnConnect(unsigned long duration);
    void actionOnDisconnect(const char* reason);

public:
    WiFiManager(IWiFiService* service, EventDispatcher* dispatcher, ICredentialsProvider* credentials, const WiFiConnectionPolicy& policy);
    ~WiFiManager() {}

    void initialize();
    void connect();
    void disconnect();
    
    /**
     * @brief Periodic update called by scheduler. Checks status,
     * monitors signal drops, and handles reconnect retries.
     */
    void update();

    bool isConnected() const;
    const char* getIPAddress() const;
    int getRSSI() const;
    const char* getMAC() const;
    
    WiFiState getState() const { return _currentState; }
    const WiFiDiagnostics& getDiagnostics() const { return _diagnostics; }
    WiFiObserverManager& getObserverManager() { return _observerManager; }
    const WiFiConnectionHistory& getHistory() const { return _history; }
};

#endif
