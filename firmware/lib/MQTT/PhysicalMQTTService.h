#ifndef PHYSICAL_MQTT_SERVICE_H
#define PHYSICAL_MQTT_SERVICE_H

#include "IMQTTService.h"
#include <WiFiClient.h>
#include <PubSubClient.h>

class PhysicalMQTTService : public IMQTTService {
private:
    WiFiClient _wifiClient;
    PubSubClient _mqttClient;
    void (*_callback)(const char* topic, const char* payload);
    char _host[64];
    int _port;
    char _clientId[32];
    char _user[32];
    char _pass[32];
    char _willTopic[64];
    char _willMessage[32];
    bool _hasConfig;

public:
    PhysicalMQTTService();
    bool connect(const MQTTConfig& config) override;
    void disconnect() override;
    bool publish(const char* topic, const char* payload, int qos = 0, bool retain = false) override;
    bool subscribe(const char* topic, int qos = 0) override;
    bool unsubscribe(const char* topic) override;
    MQTTState getStatus() override;
    void update() override;
    void setCallback(void (*callback)(const char* topic, const char* payload)) override;

    friend void pubsubCallbackRouter(char* topic, uint8_t* payload, unsigned int length);
};

#endif
