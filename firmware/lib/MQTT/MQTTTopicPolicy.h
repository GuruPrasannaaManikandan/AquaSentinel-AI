#ifndef MQTT_TOPIC_POLICY_H
#define MQTT_TOPIC_POLICY_H

#include <stddef.h>

enum class TopicPermission {
    PUBLISH_ONLY,
    SUBSCRIBE_ONLY,
    READ_WRITE
};

/**
 * @brief Class containing validations for topics, QoS constraints, and payloads.
 */
class MQTTTopicPolicy {
private:
    TopicPermission _permission;
    int _maxQoS;
    bool _allowRetain;
    size_t _maxPayloadSize;

public:
    MQTTTopicPolicy(TopicPermission perm = TopicPermission::READ_WRITE, int maxQoS = 1, bool allowRetain = true, size_t maxPayload = 128);
    ~MQTTTopicPolicy() {}

    /**
     * @brief Evaluates permissions and payload bounds before dispatching.
     */
    bool validate(const char* topic, size_t payloadSize, int qos, bool retain) const;
    
    TopicPermission getPermission() const { return _permission; }
    int getMaxQoS() const { return _maxQoS; }
    bool isRetainAllowed() const { return _allowRetain; }
    size_t getMaxPayloadSize() const { return _maxPayloadSize; }
};

#endif
