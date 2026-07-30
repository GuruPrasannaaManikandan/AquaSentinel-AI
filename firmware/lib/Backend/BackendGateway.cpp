#include "BackendGateway.h"
#include <ArduinoJson.h>
#include <Arduino.h>
#include <stdio.h>
#include <string.h>

static void getISOTimestamp(char* buffer, size_t size) {
    unsigned long long secondsSinceBase = millis() / 1000;
    unsigned long second = (8 + secondsSinceBase) % 60;
    unsigned long minutesCarrier = (8 + secondsSinceBase) / 60;
    unsigned long minute = (51 + minutesCarrier) % 60;
    unsigned long hoursCarrier = (51 + minutesCarrier) / 60;
    unsigned long hour = (13 + hoursCarrier) % 24;
    unsigned long daysCarrier = (13 + hoursCarrier) / 24;
    unsigned long day = 29 + daysCarrier;
    
    snprintf(buffer, size, "2026-07-%02luT%02lu:%02lu:%02luZ", day, hour, minute, second);
}

static void dummySubscriptionHandler(const char* payload) {
    // Handled by observer notifyMessageReceived
}

BackendGateway::BackendGateway(MQTTManager* mqttManager, EventDispatcher* dispatcher, const char* deviceId, const char* datasetRoute)
    : _mqttManager(mqttManager), _dispatcher(dispatcher) {
    
    strncpy(_deviceId, deviceId ? deviceId : "UNKNOWN", sizeof(_deviceId) - 1);
    _deviceId[sizeof(_deviceId) - 1] = '\0';

    strncpy(_datasetRoute, datasetRoute ? datasetRoute : "caml", sizeof(_datasetRoute) - 1);
    _datasetRoute[sizeof(_datasetRoute) - 1] = '\0';

    // Instantiation of refined architecture modules
    _syncState = BackendSyncState::UNREGISTERED;
    _syncPolicy = new BackendSyncPolicy();
    _offlineBuffer = new OfflineTelemetryBuffer();
    _sessionHistory = new BackendSessionHistory();
    _observerManager = new BackendObserverManager();
    _configManager = new ConfigurationManager(_syncPolicy);

    // Instantiation of integration sub-modules
    _telemetryPublisher = new TelemetryPublisher(_mqttManager, _deviceId, _datasetRoute);
    _deviceRegistration = new DeviceRegistration(_deviceId, "3.9.1", "ESP32-WROOM-32E");
    _commandHandler = new BackendCommandHandler(_dispatcher, nullptr, _mqttManager, _deviceId); // NULL HAL for Hardware Isolation
    _deviceShadow = new DeviceShadow();
    _healthMonitor = new HealthMonitor(nullptr, nullptr, _mqttManager, nullptr); // Passive health monitor
    _diagnostics = new BackendDiagnostics();

    _deviceRegistration->setCapabilities("gps,rtc,temperature,salinity,ph,turbidity,dissolved_oxygen");
    _deviceRegistration->setLocation(27.5, (strcmp(_datasetRoute, "caml") == 0) ? -81.2 : -82.5);
    _deviceShadow->updateVersions("3.9.1", "1.0");

    _isWiFiConnected = false;
    _fsmState = 0;
    _wasConnected = false;
    _sessionStartMillis = 0;

    _lastHeartbeatTime = 0;
    _lastDiagnosticsTime = 0;
    _lastTelemetryTime = 0;
}

BackendGateway::~BackendGateway() {
    delete _syncPolicy;
    delete _offlineBuffer;
    delete _sessionHistory;
    delete _observerManager;
    delete _configManager;
    delete _telemetryPublisher;
    delete _deviceRegistration;
    delete _commandHandler;
    delete _deviceShadow;
    delete _healthMonitor;
    delete _diagnostics;
}

void BackendGateway::initialize() {
    if (_mqttManager) {
        _mqttManager->getObserverManager().subscribe(this);
    }
    transitionTo(BackendSyncState::UNREGISTERED);
    Serial.println("[BACKEND-GATEWAY] Refined Integration Gateway Initialized (v3.9.1).");
}

void BackendGateway::setWiFiConnected(bool connected) {
    if (_isWiFiConnected != connected) {
        _isWiFiConnected = connected;
        Serial.print("[BACKEND-GATEWAY] WiFi Status Update: ");
        Serial.println(_isWiFiConnected ? "CONNECTED" : "DISCONNECTED");
        
        if (!_isWiFiConnected) {
            transitionTo(BackendSyncState::RECOVERING);
        }
    }
}

void BackendGateway::setFSMState(int state) {
    _fsmState = state;
    if (_deviceShadow) {
        _deviceShadow->updateFSMState(state);
    }
}

void BackendGateway::transitionTo(BackendSyncState newState) {
    if (_syncState == newState) return;

    // Check transition validity (Guards)
    bool valid = false;
    switch (newState) {
        case BackendSyncState::UNREGISTERED:
            valid = true;
            break;
        case BackendSyncState::REGISTERING:
            valid = guardWiFiConnected() && guardMQTTConnected();
            break;
        case BackendSyncState::REGISTERED:
            valid = guardRegistrationSuccessful();
            break;
        case BackendSyncState::SYNCING:
            valid = guardMQTTConnected();
            break;
        case BackendSyncState::SYNCHRONIZED:
            valid = guardMQTTConnected();
            break;
        case BackendSyncState::RECOVERING:
            valid = true;
            break;
        case BackendSyncState::FAILED:
            valid = true;
            break;
    }

    if (!valid) {
        Serial.print("[BACKEND-GATEWAY-FSM] Rejecting transition: ");
        Serial.print(getBackendSyncStateName(_syncState));
        Serial.print(" -> ");
        Serial.println(getBackendSyncStateName(newState));
        return;
    }

    BackendSyncState oldState = _syncState;
    _syncState = newState;

    Serial.print("[BACKEND-GATEWAY-FSM] State transition: ");
    Serial.print(getBackendSyncStateName(oldState));
    Serial.print(" -> ");
    Serial.println(getBackendSyncStateName(_syncState));

    // Notify observers
    _observerManager->notifySyncStateTransition(oldState, _syncState);

    // Execute actions
    switch (_syncState) {
        case BackendSyncState::REGISTERING:
            actionRegisterDevice();
            break;
        case BackendSyncState::REGISTERED:
            actionRequestConfiguration();
            break;
        case BackendSyncState::RECOVERING: {
            _diagnostics->endSession();
            
            // Record session history
            SessionHistoryItem item;
            item.timestamp = millis();
            item.sessionStartMs = _sessionStartMillis;
            item.sessionEndMs = millis();
            item.syncTimeMs = _diagnostics->getAverageSyncTimeMs();
            item.bytesSent = _diagnostics->getMessagesPublished() * 140; 
            item.bytesReceived = _diagnostics->getMessagesReceived() * 40;
            item.reconnectCount = _diagnostics->getReconnectCount();
            strcpy(item.failureReason, "Network Loss / Recovery Triggered");
            _sessionHistory->addSession(item);
            
            _wasConnected = false;
            break;
        }
        case BackendSyncState::FAILED: {
            _diagnostics->endSession();
            break;
        }
        default:
            break;
    }
}

void BackendGateway::actionRegisterDevice() {
    Serial.println("[BACKEND-GATEWAY-ACTION] Executing: Register Device");
    char regBuf[256];
    _deviceRegistration->setStatus(RegistrationStatus::REGISTERING);
    if (_deviceRegistration->serialize(regBuf, sizeof(regBuf))) {
        char regTopic[64];
        snprintf(regTopic, sizeof(regTopic), "aquatic/%s/status", _deviceId);
        bool ok = _mqttManager->publish(regTopic, regBuf, 0, true);
        if (ok) {
            _deviceRegistration->setStatus(RegistrationStatus::REGISTERED);
            _diagnostics->recordPublish();
            transitionTo(BackendSyncState::REGISTERED);
        } else {
            _deviceRegistration->setStatus(RegistrationStatus::FAILED);
            transitionTo(BackendSyncState::FAILED);
        }
    }
}

void BackendGateway::actionRequestConfiguration() {
    Serial.println("[BACKEND-GATEWAY-ACTION] Executing: Request Configuration");
    char topic[64];
    snprintf(topic, sizeof(topic), "aquatic/%s/configuration", _deviceId);
    
    // Subscribe to config updates
    _mqttManager->subscribe(topic, dummySubscriptionHandler, 0);

    // Publish sync trace
    _diagnostics->recordPublish();
    transitionTo(BackendSyncState::SYNCHRONIZED);
}

void BackendGateway::actionFlushOfflineQueue() {
    Serial.println("[BACKEND-GATEWAY-ACTION] Executing: Flush Offline Queue");
    int count = _offlineBuffer->getCount();
    TelemetryData data;
    while (_offlineBuffer->pop(data)) {
        publishTelemetry(data);
    }
    Serial.print("[BACKEND-GATEWAY] Flushed offline cached frames count: ");
    Serial.println(count);
}

void BackendGateway::update() {
    processCommandEvents();

    if (!_mqttManager) return;

    bool isConnected = _mqttManager->isConnected();

    // Connection recovery monitor
    if (isConnected && !_wasConnected) {
        Serial.println("[BACKEND-GATEWAY] Connection established. Initializing Session Sync...");
        _diagnostics->startSession();
        _sessionStartMillis = millis();
        _diagnostics->recordReconnect();
        _wasConnected = true;

        if (_syncState == BackendSyncState::RECOVERING) {
            // Re-register and flush offline buffer
            actionFlushOfflineQueue();
            transitionTo(BackendSyncState::REGISTERING);
        } else {
            transitionTo(BackendSyncState::REGISTERING);
        }
    } else if (!isConnected && _wasConnected) {
        transitionTo(BackendSyncState::RECOVERING);
    }

    // State evaluators
    if (_syncState == BackendSyncState::UNREGISTERED && guardWiFiConnected() && guardMQTTConnected()) {
        transitionTo(BackendSyncState::REGISTERING);
    }

    // Periodic tasks (heartbeat & diagnostics)
    if (isConnected && _syncState == BackendSyncState::SYNCHRONIZED) {
        unsigned long now = millis();
        if (now - _lastHeartbeatTime >= _syncPolicy->getHeartbeatIntervalMs()) {
            publishHeartbeat();
            _lastHeartbeatTime = now;
        }
        if (now - _lastDiagnosticsTime >= _syncPolicy->getDiagnosticsIntervalMs()) {
            publishDiagnostics();
            _lastDiagnosticsTime = now;
        }
    }

    checkStateChanges();
}

void BackendGateway::processCommandEvents() {
    if (!_dispatcher) return;

    FSMEvent tempEvents[10];
    int tempCount = 0;
    FSMEvent ev;

    while (_dispatcher->getQueue().dequeue(ev)) {
        int evId = static_cast<int>(ev.id);
        if (evId >= 100 && evId <= 106) {
            unsigned long startSync = millis();
            bool ok = _commandHandler->handleCommand(evId, nullptr);
            unsigned long duration = millis() - startSync;

            if (ok) {
                _diagnostics->recordSyncSuccess(duration);
            } else {
                _diagnostics->recordSyncFailure();
            }
        } else {
            if (tempCount < 10) {
                tempEvents[tempCount++] = ev;
            }
        }
    }

    for (int i = 0; i < tempCount; i++) {
        _dispatcher->getQueue().enqueue(tempEvents[i]);
    }
}

void BackendGateway::publishHeartbeat() {
    char topic[64];
    snprintf(topic, sizeof(topic), "aquatic/%s/status", _deviceId);

    StaticJsonDocument<256> doc;
    doc["device_id"] = _deviceId;
    doc["state"] = "ONLINE";
    doc["uptime"] = millis() / 1000;
    doc["sensor_status"] = _deviceShadow->getShadow().sensorStatus;
    doc["firmware_version"] = _deviceRegistration->getFirmwareVersion();
    doc["sync_state"] = getBackendSyncStateName(_syncState);

    char buffer[256];
    size_t len = serializeJson(doc, buffer, sizeof(buffer));
    if (len > 0 && len < sizeof(buffer)) {
        _mqttManager->publish(topic, buffer, 0, false);
        _diagnostics->recordPublish();
    }
}

void BackendGateway::publishDiagnostics() {
    char topic[64];
    snprintf(topic, sizeof(topic), "aquatic/%s/diagnostics", _deviceId);

    StaticJsonDocument<512> doc;
    doc["device_id"] = _deviceId;
    doc["publishes"] = _diagnostics->getMessagesPublished();
    doc["receives"] = _diagnostics->getMessagesReceived();
    doc["sync_success"] = _diagnostics->getSyncSuccess();
    doc["sync_failure"] = _diagnostics->getSyncFailure();
    doc["reconnects"] = _diagnostics->getReconnectCount();
    doc["avg_sync_time_ms"] = _diagnostics->getAverageSyncTimeMs();
    doc["success_rate_pct"] = _diagnostics->getSyncSuccessRate();
    doc["failure_rate_pct"] = _diagnostics->getSyncFailureRate();
    
    // Expanded variables
    doc["config_updates"] = _diagnostics->getConfigUpdates();
    doc["rollbacks"] = _diagnostics->getRollbackCount();
    doc["offline_buffer_usage"] = _diagnostics->getOfflineBufferUsage();
    doc["dropped_telemetry"] = _diagnostics->getDroppedTelemetry();
    doc["session_duration_sec"] = _diagnostics->getSessionDurationSeconds();

    char buffer[512];
    size_t len = serializeJson(doc, buffer, sizeof(buffer));
    if (len > 0 && len < sizeof(buffer)) {
        _mqttManager->publish(topic, buffer, 0, false);
        _diagnostics->recordPublish();
        _observerManager->notifyDiagnosticsSynced();
    }
}

void BackendGateway::checkStateChanges() {
    if (!_deviceShadow) return;
    _deviceShadow->updateNetworkStatus(guardMQTTConnected() ? "CONNECTED" : "DISCONNECTED");
}

bool BackendGateway::publishTelemetry(const TelemetryData& data) {
    if (_syncState == BackendSyncState::RECOVERING || _syncState == BackendSyncState::UNREGISTERED || !guardMQTTConnected()) {
        // Enqueue telemetry in offline circular buffer
        bool overflow = _offlineBuffer->push(data);
        _diagnostics->updateOfflineBufferUsage(_offlineBuffer->getCount());
        _observerManager->notifyTelemetryBuffered(data, _offlineBuffer->getCount());
        
        if (overflow) {
            _diagnostics->recordDroppedTelemetry();
            _observerManager->notifyTelemetryDropped(data);
            Serial.println("[BACKEND-GATEWAY-BUFFER] WARNING: Offline queue overflow. Dropped oldest frame.");
        }
        return false;
    }

    transitionTo(BackendSyncState::SYNCING);

    char ts[32];
    getISOTimestamp(ts, sizeof(ts));

    int rssi = -60;
    float battery = 98.5f;

    bool ok = _telemetryPublisher->publishTelemetry(data, battery, rssi, ts);
    if (ok) {
        _deviceShadow->updateTelemetry(data);
        _diagnostics->recordPublish();
        transitionTo(BackendSyncState::SYNCHRONIZED);
    } else {
        transitionTo(BackendSyncState::REGISTERED);
    }
    return ok;
}

bool BackendGateway::publishAlert(const char* alertType, const char* description) {
    if (!guardMQTTConnected()) return false;

    char ts[32];
    getISOTimestamp(ts, sizeof(ts));

    StaticJsonDocument<256> doc;
    doc["device_id"] = _deviceId;
    doc["alert_type"] = alertType ? alertType : "WARNING";
    doc["description"] = description ? description : "";
    doc["timestamp"] = ts;

    char buffer[256];
    size_t len = serializeJson(doc, buffer, sizeof(buffer));

    char topic[64];
    snprintf(topic, sizeof(topic), "aquatic/%s/alerts", _deviceId);

    if (len > 0 && len < sizeof(buffer)) {
        bool ok = _mqttManager->publish(topic, buffer, 1, false);
        if (ok) {
            _deviceShadow->updateLastAlert(description);
            _diagnostics->recordPublish();
        }
        return ok;
    }
    return false;
}

// Observers notification hooks
void BackendGateway::onMQTTStateTransition(MQTTState fromState, MQTTState toState) {
    if (toState == MQTTState::DISCONNECTED) {
        transitionTo(BackendSyncState::RECOVERING);
    }
}

void BackendGateway::onMessagePublished(const char* topic, const char* payload) {
}

void BackendGateway::onMessageReceived(const char* topic, const char* payload) {
    if (!topic || !payload) return;

    char cmdTopic[64];
    snprintf(cmdTopic, sizeof(cmdTopic), "aquatic/%s/command", _deviceId);
    
    char configTopic[64];
    snprintf(configTopic, sizeof(configTopic), "aquatic/%s/configuration", _deviceId);

    if (strcmp(topic, cmdTopic) == 0) {
        StaticJsonDocument<256> doc;
        DeserializationError err = deserializeJson(doc, payload);
        if (!err) {
            const char* commandName = doc["command"];
            int eventId = 0;
            if (BackendCommandHandler::parseCommandToEventId(commandName, eventId)) {
                if (_dispatcher) {
                    _dispatcher->publish(static_cast<Event>(eventId), EventSource::MQTT, EventPriority::NORMAL, nullptr);
                    _diagnostics->recordReceive();
                }
            }
        }
    } else if (strcmp(topic, configTopic) == 0) {
        // Handle incoming dynamic configuration updates
        bool success = _configManager->receiveConfiguration(payload);
        if (success) {
            _diagnostics->recordConfigUpdate();
            _observerManager->notifyConfigUpdated(_configManager->getActiveConfig().version, _configManager->getActiveConfig().telemetryIntervalMs);
        } else {
            _diagnostics->recordRollback();
        }
    }
}
