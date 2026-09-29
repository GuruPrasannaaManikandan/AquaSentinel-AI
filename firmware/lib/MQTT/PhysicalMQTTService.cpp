#include "PhysicalMQTTService.h"
#include <Arduino.h>
#include <WiFi.h>

static PhysicalMQTTService* g_physMQTTInstance = nullptr;

void pubsubCallbackRouter(char* topic, uint8_t* payload, unsigned int length) {
    if (!g_physMQTTInstance) return;
    char safeBuf[256];
    unsigned int copyLen = (length < sizeof(safeBuf) - 1) ? length : (sizeof(safeBuf) - 1);
    memcpy(safeBuf, payload, copyLen);
    safeBuf[copyLen] = '\0';
    if (g_physMQTTInstance->_callback) {
        g_physMQTTInstance->_callback(topic, safeBuf);
    }
}

PhysicalMQTTService::PhysicalMQTTService() : _mqttClient(_wifiClient), _callback(nullptr), _port(1883), _hasConfig(false) {
    g_physMQTTInstance = this;
    _mqttClient.setCallback(pubsubCallbackRouter);
    _mqttClient.setBufferSize(1024);
}

bool PhysicalMQTTService::connect(const MQTTConfig& config) {
    strncpy(_host, config.brokerAddress, sizeof(_host) - 1);
    _host[sizeof(_host) - 1] = '\0';
    _port = config.port;
    strncpy(_clientId, config.clientId, sizeof(_clientId) - 1);
    _clientId[sizeof(_clientId) - 1] = '\0';
    strncpy(_user, config.username, sizeof(_user) - 1);
    _user[sizeof(_user) - 1] = '\0';
    strncpy(_pass, config.password, sizeof(_pass) - 1);
    _pass[sizeof(_pass) - 1] = '\0';
    strncpy(_willTopic, config.lastWillTopic, sizeof(_willTopic) - 1);
    _willTopic[sizeof(_willTopic) - 1] = '\0';
    strncpy(_willMessage, config.lastWillMessage, sizeof(_willMessage) - 1);
    _willMessage[sizeof(_willMessage) - 1] = '\0';
    _hasConfig = true;

    _mqttClient.setServer(_host, _port);
    Serial.print("[PHYSICAL-MQTT] Connecting to broker: ");
    Serial.print(_host);
    Serial.print(":");
    Serial.println(_port);

    bool ok = false;
    bool hasWill = (strlen(_willTopic) > 0);
    if (strlen(_user) > 0) {
        if (hasWill) {
            ok = _mqttClient.connect(_clientId, _user, _pass, _willTopic, 0, false, _willMessage);
        } else {
            ok = _mqttClient.connect(_clientId, _user, _pass);
        }
    } else {
        if (hasWill) {
            ok = _mqttClient.connect(_clientId, _willTopic, 0, false, _willMessage);
        } else {
            ok = _mqttClient.connect(_clientId);
        }
    }
    
    if (!ok && strcmp(_host, "test.mosquitto.org") != 0) {
        Serial.print("[PHYSICAL-MQTT] LAN broker (");
        Serial.print(_host);
        Serial.println(") unreachable (client isolation/firewall). Switching to Mosquitto broker: test.mosquitto.org");
        strncpy(_host, "test.mosquitto.org", sizeof(_host) - 1);
        _host[sizeof(_host) - 1] = '\0';
        _port = 1883;
        _mqttClient.setServer(_host, 1883);
        if (hasWill) {
            ok = _mqttClient.connect(_clientId, _willTopic, 0, false, _willMessage);
        } else {
            ok = _mqttClient.connect(_clientId);
        }
    }

    if (ok) {
        Serial.print("[PHYSICAL-MQTT] Connected successfully to ");
        Serial.println(_host);
    } else {
        Serial.print("[PHYSICAL-MQTT] Connect failed, rc=");
        Serial.println(_mqttClient.state());
    }
    return ok;
}

void PhysicalMQTTService::disconnect() {
    _mqttClient.disconnect();
}

bool PhysicalMQTTService::publish(const char* topic, const char* payload, int qos, bool retain) {
    if (!_mqttClient.connected()) return false;
    return _mqttClient.publish(topic, payload, retain);
}

bool PhysicalMQTTService::subscribe(const char* topic, int qos) {
    if (!_mqttClient.connected()) return false;
    return _mqttClient.subscribe(topic, qos);
}

bool PhysicalMQTTService::unsubscribe(const char* topic) {
    if (!_mqttClient.connected()) return false;
    return _mqttClient.unsubscribe(topic);
}

MQTTState PhysicalMQTTService::getStatus() {
    if (_mqttClient.connected()) {
        return MQTTState::CONNECTED;
    }
    return MQTTState::DISCONNECTED;
}

void PhysicalMQTTService::update() {
    if (_mqttClient.connected()) {
        _mqttClient.loop();
    } else if (_hasConfig && WiFi.status() == WL_CONNECTED) {
        static unsigned long lastReconnectAttempt = 0;
        unsigned long now = millis();
        if (now - lastReconnectAttempt > 5000) {
            lastReconnectAttempt = now;
            Serial.print("[PHYSICAL-MQTT] Reconnecting to broker: ");
            Serial.println(_host);
            if (strlen(_user) > 0) {
                _mqttClient.connect(_clientId, _user, _pass, _willTopic, 0, false, _willMessage);
            } else {
                _mqttClient.connect(_clientId, _willTopic, 0, false, _willMessage);
            }
            if (!_mqttClient.connected() && strcmp(_host, "test.mosquitto.org") != 0) {
                strncpy(_host, "test.mosquitto.org", sizeof(_host) - 1);
                _host[sizeof(_host) - 1] = '\0';
                _port = 1883;
                _mqttClient.setServer(_host, 1883);
                Serial.println("[PHYSICAL-MQTT] Switched to test.mosquitto.org for reconnection");
            }
        }
    }
}

void PhysicalMQTTService::setCallback(void (*callback)(const char* topic, const char* payload)) {
    _callback = callback;
}
