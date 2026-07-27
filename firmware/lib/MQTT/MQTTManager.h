#ifndef MQTT_MANAGER_H
#define MQTT_MANAGER_H

#include "IMQTTService.h"
#include "MQTTConfig.h"
#include "MQTTTopicRegistry.h"
#include "MQTTPublishQueue.h"
#include "MQTTSubscriptionManager.h"
#include "MQTTObserverManager.h"
#include "MQTTDiagnostics.h"
#include "MQTTCommandDispatcher.h"
#include "WiFiManager.h"
#include "MQTTTopicPolicy.h"
#include "MQTTQoSPolicy.h"
#include "MQTTMessageHistory.h"
#include "MQTTConnectionObserverManager.h"
#include "config/TelemetryData.h"

class MQTTManager {
private:
    IMQTTService* _service;
    EventDispatcher* _dispatcher;
    WiFiManager* _wifiManager;
    MQTTConfig _config;
    MQTTTopicRegistry _topics;

    MQTTTopicPolicy _topicPolicy;
    MQTTQoSPolicy _qosPolicy;
    MQTTMessageHistory _messageHistory;
    MQTTConnectionObserverManager _connObserverManager;

    MQTTState _currentState;
    MQTTPublishQueue _publishQueue;
    MQTTSubscriptionManager _subManager;
    MQTTObserverManager _observerManager;
    MQTTDiagnostics _diagnostics;
    MQTTCommandDispatcher _commandDispatcher;

    unsigned long _connectingTimeStart;
    unsigned long _sessionStartTimeMs;
    unsigned long _lastHeartbeatTime;
    unsigned long _totalPublishes;
    unsigned long _totalPublishTimeMs;
    unsigned long _totalSessionTimeMs;

    void processPublishQueue();
    void sendHeartbeat();
    
    // Internal transitions actions
    void actionOnConnect();
    void actionOnDisconnect(const char* reason);

public:
    MQTTManager(IMQTTService* service, EventDispatcher* dispatcher, WiFiManager* wifiManager, const MQTTConfig& config, const MQTTTopicRegistry& topics, const MQTTTopicPolicy& topicPolicy, const MQTTQoSPolicy& qosPolicy);
    ~MQTTManager() {}

    void initialize();
    void connect();
    void disconnect();
    
    /**
     * @brief Periodic update called by scheduler. Evaluates Wi-Fi state,
     * processes handshakes, drains publish queues, and sends heartbeats.
     */
    void update();

    bool publish(const char* topic, const char* payload, int qos = 0, bool retain = false);
    bool subscribe(const char* topic, void (*handler)(const char* payload), int qos = 0);
    
    /**
     * @brief Encodes and enqueues structured sensor telemetry.
     */
    bool publishTelemetry(const TelemetryData& data);
    
    /**
     * @brief Encodes and enqueues system diagnostics.
     */
    bool publishDiagnostics();

    bool isConnected() const;
    MQTTState getState() const { return _currentState; }
    const MQTTDiagnostics& getDiagnostics() const { return _diagnostics; }
    MQTTObserverManager& getObserverManager() { return _observerManager; }
    MQTTConnectionObserverManager& getConnectionObserverManager() { return _connObserverManager; }
    const MQTTMessageHistory& getMessageHistory() const { return _messageHistory; }
    MQTTCommandDispatcher& getCommandDispatcher() { return _commandDispatcher; }
    MQTTPublishQueue& getPublishQueue() { return _publishQueue; }

    void routeIncomingMessage(const char* topic, const char* payload);
};

#endif
