#include "MQTTTopicPolicy.h"
#include <string.h>
#include <Arduino.h>

MQTTTopicPolicy::MQTTTopicPolicy(TopicPermission perm, int maxQoS, bool allowRetain, size_t maxPayload)
    : _permission(perm), _maxQoS(maxQoS), _allowRetain(allowRetain), _maxPayloadSize(maxPayload) {}

bool MQTTTopicPolicy::validate(const char* topic, size_t payloadSize, int qos, bool retain) const {
    if (!topic || strlen(topic) == 0) {
        Serial.println("[MQTT-POLICY] Validation error: Empty topic path.");
        return false;
    }
    
    if (payloadSize > _maxPayloadSize) {
        Serial.print("[MQTT-POLICY] Validation error: Payload exceeds limit of ");
        Serial.print(_maxPayloadSize);
        Serial.print(" bytes. Attempted: ");
        Serial.println(payloadSize);
        return false;
    }

    if (qos > _maxQoS) {
        Serial.print("[MQTT-POLICY] Validation error: QoS level ");
        Serial.print(qos);
        Serial.print(" exceeds policy max of ");
        Serial.println(_maxQoS);
        return false;
    }

    if (retain && !_allowRetain) {
        Serial.println("[MQTT-POLICY] Validation error: Retain flag violates policy.");
        return false;
    }

    return true;
}
