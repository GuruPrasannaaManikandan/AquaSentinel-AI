#include "MQTTManager.h"
#include "MQTTSerializer.h"
#include <Arduino.h>
#include <string.h>

#ifdef LOW
#undef LOW
#endif
#ifdef HIGH
#undef HIGH
#endif
#ifdef DISABLED
#undef DISABLED
#endif

static MQTTManager* g_mqttManagerInstance = nullptr;

static void globalMQTTCallback(const char* topic, const char* payload) {
    if (g_mqttManagerInstance) {
        g_mqttManagerInstance->routeIncomingMessage(topic, payload);
    }
}

MQTTManager::MQTTManager(IMQTTService* service, EventDispatcher* dispatcher, WiFiManager* wifiManager, const MQTTConfig& config, const MQTTTopicRegistry& topics, const MQTTTopicPolicy& topicPolicy, const MQTTQoSPolicy& qosPolicy)
    : _service(service), _dispatcher(dispatcher), _wifiManager(wifiManager), _config(config), _topics(topics),
      _topicPolicy(topicPolicy), _qosPolicy(qosPolicy),
      _currentState(MQTTState::DISCONNECTED), _subManager(service), _commandDispatcher(dispatcher),
      _connectingTimeStart(0), _sessionStartTimeMs(0), _lastHeartbeatTime(0),
      _totalPublishes(0), _totalPublishTimeMs(0), _totalSessionTimeMs(0) {
    
    memset(&_diagnostics, 0, sizeof(_diagnostics));
    strcpy(_diagnostics.lastError, "None");
    _diagnostics.publishSuccessRate = 100.0f;
}

void MQTTManager::initialize() {
    g_mqttManagerInstance = this;
    _service->setCallback(globalMQTTCallback);
    
    disconnect();
    _currentState = MQTTState::DISCONNECTED;
    
    memset(&_diagnostics, 0, sizeof(_diagnostics));
    _diagnostics.publishSuccessRate = 100.0f;
}

void MQTTManager::connect() {
    if (!_wifiManager->isConnected() || _currentState == MQTTState::CONNECTED || _currentState == MQTTState::CONNECTING) {
        return;
    }

    MQTTState prev = _currentState;
    _currentState = MQTTState::CONNECTING;
    _connectingTimeStart = millis();
    _service->connect(_config);

    if (prev == MQTTState::RECONNECTING) {
        _connObserverManager.notifyReconnect();
    }

    if (_dispatcher) {
        _dispatcher->publish(Event::MQTT_CONNECT_REQUEST, EventSource::MQTT, EventPriority::NORMAL);
    }
    _observerManager.notifyStateTransition(prev, MQTTState::CONNECTING);
}

void MQTTManager::disconnect() {
    MQTTState prev = _currentState;
    _service->disconnect();
    _currentState = MQTTState::DISCONNECTED;

    actionOnDisconnect("User Request");
    
    _observerManager.notifyStateTransition(prev, MQTTState::DISCONNECTED);
}

void MQTTManager::actionOnConnect() {
    _diagnostics.connectionCount++;
    _diagnostics.brokerSessions++;
    _sessionStartTimeMs = millis();
    _lastHeartbeatTime = millis();

    // Subscribe to commands topic
    _service->subscribe(_topics.commands, _qosPolicy.getQoSLevel());
    _diagnostics.subscribeCount++;

    _connObserverManager.notifyConnected();

    if (_dispatcher) {
        _dispatcher->publish(Event::MQTT_CONNECTED, EventSource::MQTT, EventPriority::HIGH);
    }
}

void MQTTManager::actionOnDisconnect(const char* reason) {
    unsigned long sessionDuration = 0;
    if (_sessionStartTimeMs > 0) {
        sessionDuration = millis() - _sessionStartTimeMs;
        _totalSessionTimeMs += sessionDuration;
        _diagnostics.averageSessionMs = _totalSessionTimeMs / _diagnostics.brokerSessions;
        
        if (sessionDuration > _diagnostics.longestSessionMs) {
            _diagnostics.longestSessionMs = sessionDuration;
        }
        if (sessionDuration < _diagnostics.shortestSessionMs || _diagnostics.shortestSessionMs == 0) {
            _diagnostics.shortestSessionMs = sessionDuration;
        }
        _sessionStartTimeMs = 0;
    }

    strncpy(_diagnostics.lastError, reason, 31);
    _diagnostics.lastError[31] = '\0';

    if (strcmp(reason, "Broker Link Loss") == 0) {
        _connObserverManager.notifyBrokerLost();
    } else {
        _connObserverManager.notifyDisconnected();
    }

    if (_dispatcher) {
        _dispatcher->publish(Event::MQTT_DISCONNECTED, EventSource::MQTT, EventPriority::CRITICAL);
    }
}

bool MQTTManager::publish(const char* topic, const char* payload, int qos, bool retain) {
    size_t payloadSize = payload ? strlen(payload) : 0;
    
    // Topic validation check using the policy rules
    if (!_topicPolicy.validate(topic, payloadSize, qos, retain)) {
        _diagnostics.droppedMessages++;
        strcpy(_diagnostics.lastError, "Policy Rejected");
        return false;
    }

    bool enqueued = _publishQueue.enqueue(topic, payload, qos, retain);
    if (enqueued) {
        _diagnostics.totalBytesSent += payloadSize;
    } else {
        _diagnostics.droppedMessages++;
        strcpy(_diagnostics.lastError, "Queue Overflow");
    }
    return enqueued;
}

bool MQTTManager::publishTelemetry(const TelemetryData& data) {
    char buffer[128];
    if (MQTTSerializer::serializeTelemetry(data, buffer, sizeof(buffer))) {
        return publish(_topics.telemetry, buffer, _qosPolicy.getQoSLevel(), false);
    }
    return false;
}

bool MQTTManager::publishDiagnostics() {
    char buffer[192];
    if (MQTTSerializer::serializeDiagnostics(_diagnostics, buffer, sizeof(buffer))) {
        return publish(_topics.diagnostics, buffer, 0, false);
    }
    return false;
}

bool MQTTManager::subscribe(const char* topic, void (*handler)(const char* payload), int qos) {
    bool ok = _subManager.subscribe(topic, handler, qos);
    if (ok) {
        _diagnostics.subscribeCount++;
        if (_dispatcher) {
            _dispatcher->publish(Event::MQTT_SUBSCRIBED, EventSource::MQTT, EventPriority::LOW);
        }
    }
    return ok;
}

void MQTTManager::routeIncomingMessage(const char* topic, const char* payload) {
    size_t payloadSize = payload ? strlen(payload) : 0;
    _diagnostics.totalBytesReceived += payloadSize;
    
    _observerManager.notifyMessageReceived(topic, payload);
    
    if (_dispatcher) {
        _dispatcher->publish(Event::MQTT_MESSAGE_RECEIVED, EventSource::MQTT, EventPriority::HIGH);
    }

    // Router matching commands topic
    if (strcmp(topic, _topics.commands) == 0) {
        char cmdOut[32];
        if (MQTTSerializer::parseCommand(payload, cmdOut, sizeof(cmdOut))) {
            _commandDispatcher.handleCommand(cmdOut);
        }
    } else {
        _subManager.dispatchMessage(topic, payload);
    }
}

void MQTTManager::processPublishQueue() {
    MQTTPublishItem item;
    while (_publishQueue.peek(item)) {
        unsigned long startMs = millis();
        bool ok = _service->publish(item.topic, item.payload, item.qos, item.retain);
        
        if (ok) {
            unsigned long duration = millis() - startMs;
            _totalPublishes++;
            _totalPublishTimeMs += duration;

            _diagnostics.publishCount++;
            _diagnostics.averagePublishLatencyMs = _totalPublishTimeMs / _totalPublishes;
            _diagnostics.averagePublishTimeMs = _diagnostics.averagePublishLatencyMs;

            _observerManager.notifyMessagePublished(item.topic, item.payload);
            _messageHistory.addRecord(item.topic, "OUT", strlen(item.payload), item.qos, item.retain, true, duration);

            if (_dispatcher) {
                _dispatcher->publish(Event::MQTT_PUBLISH_SUCCESS, EventSource::MQTT, EventPriority::LOW);
            }

            _publishQueue.removeHead();
        } else {
            // Increment retries
            MQTTPublishItem retryItem;
            _publishQueue.dequeue(retryItem);
            retryItem.retryCount++;
            _diagnostics.messageRetryCount++;

            if (retryItem.retryCount >= _qosPolicy.getMaxRetries()) {
                _diagnostics.droppedMessages++;
                strcpy(_diagnostics.lastError, "Max Retries Exceeded");
                _messageHistory.addRecord(retryItem.topic, "OUT", strlen(retryItem.payload), retryItem.qos, retryItem.retain, false, 0);
                
                if (_dispatcher) {
                    _dispatcher->publish(Event::MQTT_PUBLISH_FAILED, EventSource::MQTT, EventPriority::HIGH);
                }
            } else {
                // Re-enqueue at the tail
                _publishQueue.enqueue(retryItem.topic, retryItem.payload, retryItem.qos, retryItem.retain);
            }
            break; // Stop queue process to retry on next tick
        }
    }

    // Success Rate Calculation
    unsigned long totalAttempts = _diagnostics.publishCount + _diagnostics.droppedMessages;
    if (totalAttempts > 0) {
        _diagnostics.publishSuccessRate = ((float)_diagnostics.publishCount / (float)totalAttempts) * 100.0f;
    }
}

void MQTTManager::sendHeartbeat() {
    char payload[32];
    sprintf(payload, "Uptime: %lu S", millis() / 1000);
    publish(_topics.heartbeat, payload, 0, false);
    _lastHeartbeatTime = millis();
}

void MQTTManager::update() {
    _service->update();
    MQTTState rawStatus = _service->getStatus();
    unsigned long nowMs = millis();

    // WiFi connectivity verification
    if (!_wifiManager->isConnected()) {
        if (_currentState != MQTTState::DISCONNECTED) {
            _diagnostics.brokerDisconnects++;
            strcpy(_diagnostics.lastError, "Wi-Fi Disconnected");
            actionOnDisconnect("Wi-Fi Lost");
            _currentState = MQTTState::DISCONNECTED;
        }
        return;
    }

    switch (_currentState) {
        case MQTTState::DISCONNECTED: {
            connect();
            break;
        }

        case MQTTState::CONNECTING: {
            if (rawStatus == MQTTState::CONNECTED) {
                _currentState = MQTTState::CONNECTED;
                actionOnConnect();
            } 
            else if (nowMs - _connectingTimeStart >= 5000) {
                _diagnostics.failureCount++;
                strcpy(_diagnostics.lastError, "Handshake Timeout");
                _currentState = MQTTState::FAILED;
                
                if (_dispatcher) {
                    _dispatcher->publish(Event::MQTT_TIMEOUT, EventSource::MQTT, EventPriority::HIGH);
                }
                disconnect();
            }
            break;
        }

        case MQTTState::CONNECTED: {
            if (rawStatus == MQTTState::DISCONNECTED) {
                _currentState = MQTTState::RECONNECTING;
                _diagnostics.reconnectCount++;
                _diagnostics.brokerDisconnects++;
                actionOnDisconnect("Broker Link Loss");
            } else {
                // Drain publish queues
                processPublishQueue();

                // Send heartbeat keepalive
                if (nowMs - _lastHeartbeatTime >= _config.keepAliveIntervalS * 1000) {
                    sendHeartbeat();
                }
            }
            break;
        }

        case MQTTState::RECONNECTING:
        case MQTTState::FAILED: {
            if (nowMs - _connectingTimeStart >= _config.reconnectIntervalMs) {
                Serial.println("[MQTT-MANAGER] Reconnecting broker connection...");
                connect();
            }
            break;
        }

        case MQTTState::DISABLED:
            break;
    }

    // Keep diagnostics in sync
    _diagnostics.currentState = _currentState;
    _diagnostics.queueDepth = _publishQueue.getCount();
}

bool MQTTManager::isConnected() const {
    return _currentState == MQTTState::CONNECTED;
}
