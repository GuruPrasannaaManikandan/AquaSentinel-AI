#include "MQTTQoSPolicy.h"

MQTTQoSPolicy::MQTTQoSPolicy(int qos, unsigned long ackTimeout, int maxRetries)
    : _qosLevel(qos), _acknowledgementTimeoutMs(ackTimeout), _maxRetries(maxRetries) {}
