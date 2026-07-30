#ifndef BACKEND_COMMAND_HANDLER_H
#define BACKEND_COMMAND_HANDLER_H

#include "EventDispatcher.h"
#include "hal/HAL.h"
#include "MQTTManager.h"

// Define custom event numbers for backend commands
#define CMD_EVENT_START 100
#define CMD_EVENT_STOP 101
#define CMD_EVENT_CALIBRATE 102
#define CMD_EVENT_RESET 103
#define CMD_EVENT_PING 104
#define CMD_EVENT_HEARTBEAT 105
#define CMD_EVENT_OTA_READY 106

class BackendCommandHandler {
private:
    EventDispatcher* _dispatcher;
    HAL* _hal;
    MQTTManager* _mqttManager;
    char _deviceId[32];

public:
    BackendCommandHandler(EventDispatcher* dispatcher, HAL* hal, MQTTManager* mqttManager, const char* deviceId);
    ~BackendCommandHandler() {}

    /**
     * @brief Checks if a command string is valid and translates it to a custom Event cast.
     */
    static bool parseCommandToEventId(const char* commandName, int& eventIdOut);

    /**
     * @brief Executes the corresponding command behavior.
     */
    bool handleCommand(int eventId, const char* payload);
};

#endif // BACKEND_COMMAND_HANDLER_H
