#ifndef MQTT_QOS_POLICY_H
#define MQTT_QOS_POLICY_H

/**
 * @brief Class containing settings governing publish reliability levels.
 */
class MQTTQoSPolicy {
private:
    int _qosLevel;
    unsigned long _acknowledgementTimeoutMs;
    int _maxRetries;

public:
    MQTTQoSPolicy(int qos = 0, unsigned long ackTimeout = 2000, int maxRetries = 3);
    ~MQTTQoSPolicy() {}

    int getQoSLevel() const { return _qosLevel; }
    unsigned long getAckTimeout() const { return _acknowledgementTimeoutMs; }
    int getMaxRetries() const { return _maxRetries; }
};

#endif
