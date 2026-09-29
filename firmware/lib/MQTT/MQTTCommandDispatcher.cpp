#include "MQTTCommandDispatcher.h"
#include <string.h>
#include <Arduino.h>

#ifdef HIGH
#undef HIGH
#endif

MQTTCommandDispatcher::MQTTCommandDispatcher(EventDispatcher* dispatcher) : _dispatcher(dispatcher) {}

bool MQTTCommandDispatcher::handleCommand(const char* payload) {
    if (!payload || !_dispatcher) return false;

    Serial.print("[MQTT-COMMAND] Handling Incoming Payload: ");
    Serial.println(payload);

    // Validate and parse incoming commands
    if (strcmp(payload, "SHUTDOWN") == 0) {
        Serial.println("[MQTT-COMMAND] Valid command received: SHUTDOWN");
        return _dispatcher->publish(Event::SHUTDOWN_REQUEST, EventSource::MQTT, EventPriority::CRITICAL);
    } 
    else if (strcmp(payload, "RECOVER") == 0) {
        Serial.println("[MQTT-COMMAND] Valid command received: RECOVER");
        return _dispatcher->publish(Event::TIMEOUT, EventSource::MQTT, EventPriority::HIGH);
    }
    else if (strcmp(payload, "POLL") == 0) {
        Serial.println("[MQTT-COMMAND] Valid command received: POLL");
        return _dispatcher->publish(Event::SENSORS_READY, EventSource::MQTT, EventPriority::NORMAL);
    }

    Serial.println("[MQTT-COMMAND] ERROR: Malformed or unverified command payload received.");
    return false;
}
