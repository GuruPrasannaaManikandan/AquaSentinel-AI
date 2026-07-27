#ifndef MOCK_MQTT_SERVICE_H
#define MOCK_MQTT_SERVICE_H

#include "IMQTTService.h"

class MockMQTTService : public IMQTTService {
private:
    MQTTState _status;
    unsigned long _connectingTimeStart;
    void (*_callback)(const char* topic, const char* payload);

public:
    MockMQTTService();
    ~MockMQTTService() override {}

    bool connect(const MQTTConfig& config) override;
    void disconnect() override;
    
    bool publish(const char* topic, const char* payload, int qos = 0, bool retain = false) override;
    bool subscribe(const char* topic, int qos = 0) override;
    bool unsubscribe(const char* topic) override;
    
    MQTTState getStatus() override { return _status; }
    void update() override;
    
    void setCallback(void (*callback)(const char* topic, const char* payload)) override;

    // Helper to test incoming commands
    void simulateIncomingMessage(const char* topic, const char* payload);
};

#endif
