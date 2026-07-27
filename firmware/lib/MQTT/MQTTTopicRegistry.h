#ifndef MQTT_TOPIC_REGISTRY_H
#define MQTT_TOPIC_REGISTRY_H

/**
 * @brief Configuration mapping for all MQTT publish/subscribe topics.
 */
struct MQTTTopicRegistry {
    char telemetry[64];
    char alerts[64];
    char commands[64];
    char diagnostics[64];
    char heartbeat[64];
    char firmware[64];
    char configuration[64];
};

#endif
