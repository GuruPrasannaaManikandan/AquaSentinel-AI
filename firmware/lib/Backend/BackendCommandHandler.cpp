#include "BackendCommandHandler.h"
#include <Arduino.h>
#include <ArduinoJson.h>
#include <string.h>

BackendCommandHandler::BackendCommandHandler(EventDispatcher* dispatcher, HAL* hal, MQTTManager* mqttManager, const char* deviceId)
    : _dispatcher(dispatcher), _hal(hal), _mqttManager(mqttManager) {
    strncpy(_deviceId, deviceId ? deviceId : "UNKNOWN", sizeof(_deviceId) - 1);
    _deviceId[sizeof(_deviceId) - 1] = '\0';
}

bool BackendCommandHandler::parseCommandToEventId(const char* commandName, int& eventIdOut) {
    if (!commandName) return false;
    
    if (strcmp(commandName, "START") == 0) {
        eventIdOut = CMD_EVENT_START;
        return true;
    } else if (strcmp(commandName, "STOP") == 0) {
        eventIdOut = CMD_EVENT_STOP;
        return true;
    } else if (strcmp(commandName, "CALIBRATE") == 0) {
        eventIdOut = CMD_EVENT_CALIBRATE;
        return true;
    } else if (strcmp(commandName, "RESET") == 0) {
        eventIdOut = CMD_EVENT_RESET;
        return true;
    } else if (strcmp(commandName, "PING") == 0) {
        eventIdOut = CMD_EVENT_PING;
        return true;
    } else if (strcmp(commandName, "HEARTBEAT") == 0) {
        eventIdOut = CMD_EVENT_HEARTBEAT;
        return true;
    } else if (strcmp(commandName, "OTA_READY") == 0) {
        eventIdOut = CMD_EVENT_OTA_READY;
        return true;
    }
    return false;
}

bool BackendCommandHandler::handleCommand(int eventId, const char* payload) {
    Serial.print("[BACKEND-COMMAND-EXEC] Executing Command Event ID: ");
    Serial.println(eventId);

    switch (eventId) {
        case CMD_EVENT_START: {
            Serial.println("[BACKEND-COMMAND-EXEC] START -> Transitioning FSM to SENSING/MONITORING.");
            if (_dispatcher) {
                // SENSORS_READY triggers transition from IDLE -> MONITORING
                _dispatcher->publish(Event::SENSORS_READY, EventSource::MQTT, EventPriority::NORMAL);
            }
            return true;
        }
        case CMD_EVENT_STOP: {
            Serial.println("[BACKEND-COMMAND-EXEC] STOP -> Transitioning FSM to SHUTDOWN.");
            if (_dispatcher) {
                _dispatcher->publish(Event::SHUTDOWN_REQUEST, EventSource::MQTT, EventPriority::CRITICAL);
            }
            return true;
        }
        case CMD_EVENT_CALIBRATE: {
            Serial.println("[BACKEND-COMMAND-EXEC] CALIBRATE -> Checking sensor calibration...");
            if (_dispatcher) {
                _dispatcher->publish(Event::SENSORS_READY, EventSource::MQTT, EventPriority::NORMAL);
            }
            return true;
        }
        case CMD_EVENT_RESET: {
            Serial.println("[BACKEND-COMMAND-EXEC] RESET -> Restarting ESP32 device.");
            Serial.flush();
            #if defined(ESP32) || defined(ARDUINO_ARCH_ESP32)
            ESP.restart();
            #else
            if (_dispatcher) {
                _dispatcher->publish(Event::BOOT_COMPLETE, EventSource::MQTT, EventPriority::CRITICAL);
            }
            #endif
            return true;
        }
        case CMD_EVENT_PING: {
            Serial.println("[BACKEND-COMMAND-EXEC] PING -> Replying PONG.");
            if (_mqttManager && _mqttManager->isConnected()) {
                char topic[64];
                snprintf(topic, sizeof(topic), "aquatic/%s/status", _deviceId);
                
                StaticJsonDocument<128> doc;
                doc["status"] = "pong";
                doc["device_id"] = _deviceId;
                
                char buffer[128];
                serializeJson(doc, buffer, sizeof(buffer));
                _mqttManager->publish(topic, buffer, 0, false);
            }
            return true;
        }
        case CMD_EVENT_HEARTBEAT: {
            Serial.println("[BACKEND-COMMAND-EXEC] HEARTBEAT command acknowledged.");
            return true;
        }
        case CMD_EVENT_OTA_READY: {
            Serial.println("[BACKEND-COMMAND-EXEC] OTA_READY -> Acknowledged (Future OTA update feature support).");
            return true;
        }
        default:
            Serial.println("[BACKEND-COMMAND-EXEC] ERROR: Unknown command Event ID.");
            return false;
    }
}
