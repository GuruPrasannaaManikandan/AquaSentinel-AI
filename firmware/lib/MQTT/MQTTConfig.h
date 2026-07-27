#ifndef MQTT_CONFIG_H
#define MQTT_CONFIG_H

/**
 * @brief Structure containing broker address, credentials, and parameters.
 */
struct MQTTConfig {
    char brokerAddress[64];
    int port;
    char clientId[32];
    char username[32];
    char password[64];
    unsigned long keepAliveIntervalS;
    bool cleanSession;
    int qosDefault;
    unsigned long reconnectIntervalMs;
    char lastWillTopic[64];
    char lastWillMessage[64];
};

#endif
