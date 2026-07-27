#ifndef MQTT_COMMAND_DISPATCHER_H
#define MQTT_COMMAND_DISPATCHER_H

#include "EventDispatcher.h"

/**
 * @brief Parses incoming commands and publishes events to FSM.
 */
class MQTTCommandDispatcher {
private:
    EventDispatcher* _dispatcher;

public:
    MQTTCommandDispatcher(EventDispatcher* dispatcher);
    ~MQTTCommandDispatcher() {}

    /**
     * @brief Parses and validates incoming command payloads.
     */
    bool handleCommand(const char* payload);
};

#endif
