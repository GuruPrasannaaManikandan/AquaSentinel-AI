#ifndef BACKEND_GATEWAY_H
#define BACKEND_GATEWAY_H

#include "IMQTTObserver.h"
#include "MQTTManager.h"
#include "EventDispatcher.h"
#include "TelemetryPublisher.h"
#include "DeviceRegistration.h"
#include "BackendCommandHandler.h"
#include "DeviceShadow.h"
#include "HealthMonitor.h"
#include "BackendDiagnostics.h"
#include "BackendSyncPolicy.h"
#include "OfflineTelemetryBuffer.h"
#include "BackendSessionHistory.h"
#include "BackendSyncState.h"
#include "BackendObserverManager.h"
#include "ConfigurationManager.h"

/**
 * @brief Gateway implementing cloud sync state machine, offline buffering, configuration rollback, and hardware isolation.
 */
class BackendGateway : public IMQTTObserver {
private:
    MQTTManager* _mqttManager;
    EventDispatcher* _dispatcher;

    char _deviceId[32];
    char _datasetRoute[16];

    // Synchronization state FSM
    BackendSyncState _syncState;

    // Refinement modules
    BackendSyncPolicy* _syncPolicy;
    OfflineTelemetryBuffer* _offlineBuffer;
    BackendSessionHistory* _sessionHistory;
    BackendObserverManager* _observerManager;
    ConfigurationManager* _configManager;
    
    // Legacy integration sub-modules
    TelemetryPublisher* _telemetryPublisher;
    DeviceRegistration* _deviceRegistration;
    BackendCommandHandler* _commandHandler;
    DeviceShadow* _deviceShadow;
    HealthMonitor* _healthMonitor;
    BackendDiagnostics* _diagnostics;

    // Passive inputs representing the state of hardware (isolated)
    bool _isWiFiConnected;
    int _fsmState;
    bool _wasConnected;

    // Session stats tracking
    unsigned long _sessionStartMillis;

    // Periodic timers
    unsigned long _lastHeartbeatTime;
    unsigned long _lastDiagnosticsTime;
    unsigned long _lastTelemetryTime;

    void processCommandEvents();
    void publishHeartbeat();
    void publishDiagnostics();
    void checkStateChanges();

    // Deterministic state machine transitions
    void transitionTo(BackendSyncState newState);

    // Sync Actions
    void actionRegisterDevice();
    void actionPublishDiagnostics();
    void actionRequestConfiguration();
    void actionFlushOfflineQueue();

    // Sync Guards
    bool guardWiFiConnected() const { return _isWiFiConnected; }
    bool guardMQTTConnected() const { return _mqttManager && _mqttManager->isConnected(); }
    bool guardRegistrationSuccessful() const { return _deviceRegistration->getStatus() == RegistrationStatus::REGISTERED; }
    bool guardConfigurationValid() const { return strlen(_configManager->getActiveConfig().version) > 0; }

public:
    BackendGateway(MQTTManager* mqttManager, EventDispatcher* dispatcher, const char* deviceId, const char* datasetRoute);
    ~BackendGateway();

    void initialize();
    void update();

    // Passive setters enforcing complete Hardware Isolation
    void setWiFiConnected(bool connected);
    void setFSMState(int state);

    // IMQTTObserver callbacks
    void onMQTTStateTransition(MQTTState fromState, MQTTState toState) override;
    void onMessagePublished(const char* topic, const char* payload) override;
    void onMessageReceived(const char* topic, const char* payload) override;

    // Telemetry and Alert publishing
    bool publishTelemetry(const TelemetryData& data);
    bool publishAlert(const char* alertType, const char* description);

    // Getters
    BackendSyncState getSyncState() const { return _syncState; }
    BackendSyncPolicy* getSyncPolicy() { return _syncPolicy; }
    OfflineTelemetryBuffer* getOfflineBuffer() { return _offlineBuffer; }
    BackendSessionHistory* getSessionHistory() { return _sessionHistory; }
    BackendObserverManager* getObserverManager() { return _observerManager; }
    ConfigurationManager* getConfigManager() { return _configManager; }
    TelemetryPublisher* getTelemetryPublisher() { return _telemetryPublisher; }
    DeviceRegistration* getDeviceRegistration() { return _deviceRegistration; }
    BackendCommandHandler* getCommandHandler() { return _commandHandler; }
    DeviceShadow* getDeviceShadow() { return _deviceShadow; }
    HealthMonitor* getHealthMonitor() { return _healthMonitor; }
    BackendDiagnostics* getDiagnostics() { return _diagnostics; }
};

#endif // BACKEND_GATEWAY_H
