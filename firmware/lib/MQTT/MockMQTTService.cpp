#include "MockMQTTService.h"
#include <Arduino.h>

MockMQTTService::MockMQTTService() : _status(MQTTState::DISCONNECTED), _connectingTimeStart(0), _callback(nullptr) {}

bool MockMQTTService::connect(const MQTTConfig& config) {
    if (_status == MQTTState::CONNECTED) return true;
    
    Serial.print("[MOCK-MQTT] Connecting to Broker: ");
    Serial.print(config.brokerAddress);
    Serial.print(":");
    Serial.println(config.port);
    
    _status = MQTTState::CONNECTING;
    _connectingTimeStart = millis();
    return true;
}

void MockMQTTService::disconnect() {
    Serial.println("[MOCK-MQTT] Disconnecting from Broker...");
    _status = MQTTState::DISCONNECTED;
}

bool MockMQTTService::publish(const char* topic, const char* payload, int qos, bool retain) {
    Serial.print("[MOCK-MQTT] PUBLISH | Topic: ");
    Serial.print(topic);
    Serial.print(" | Payload: ");
    Serial.print(payload);
    Serial.print(" | QoS: ");
    Serial.println(qos);
    return true;
}

bool MockMQTTService::subscribe(const char* topic, int qos) {
    Serial.print("[MOCK-MQTT] SUBSCRIBE | Topic: ");
    Serial.print(topic);
    Serial.print(" | QoS: ");
    Serial.println(qos);
    return true;
}

bool MockMQTTService::unsubscribe(const char* topic) {
    Serial.print("[MOCK-MQTT] UNSUBSCRIBE | Topic: ");
    Serial.println(topic);
    return true;
}

void MockMQTTService::setCallback(void (*callback)(const char* topic, const char* payload)) {
    _callback = callback;
}

void MockMQTTService::simulateIncomingMessage(const char* topic, const char* payload) {
    if (_callback) {
        Serial.print("[MOCK-MQTT] Incoming Remote Message | Topic: ");
        Serial.print(topic);
        Serial.print(" | Payload: ");
        Serial.println(payload);
        _callback(topic, payload);
    }
}

void MockMQTTService::update() {
    unsigned long nowMs = millis();

    if (_status == MQTTState::CONNECTING) {
        // Simulate a 1.5-second handshake delay
        if (nowMs - _connectingTimeStart >= 1500) {
            _status = MQTTState::CONNECTED;
            Serial.println("[MOCK-MQTT] Broker connection established.");
        }
    }
}
