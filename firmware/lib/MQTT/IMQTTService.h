#ifndef IMQTT_SERVICE_H
#define IMQTT_SERVICE_H

#include "MQTTState.h"
#include "MQTTConfig.h"

/**
 * @brief Abstract interface representing general MQTT clients.
 */
class IMQTTService {
public:
    virtual ~IMQTTService() {}

    virtual bool connect(const MQTTConfig& config) = 0;
    virtual void disconnect() = 0;
    
    virtual bool publish(const char* topic, const char* payload, int qos = 0, bool retain = false) = 0;
    virtual bool subscribe(const char* topic, int qos = 0) = 0;
    virtual bool unsubscribe(const char* topic) = 0;
    
    virtual MQTTState getStatus() = 0;
    virtual void update() = 0;
    
    /**
     * @brief Registers subscription message callback.
     */
    virtual void setCallback(void (*callback)(const char* topic, const char* payload)) = 0;
};

#endif
