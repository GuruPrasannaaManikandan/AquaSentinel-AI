#include "MQTTPublishQueue.h"
#include <string.h>

MQTTPublishQueue::MQTTPublishQueue() : _head(0), _tail(0), _count(0), _droppedCount(0) {}

bool MQTTPublishQueue::enqueue(const char* topic, const char* payload, int qos, bool retain) {
    if (isFull()) {
        _droppedCount++;
        return false;
    }

    MQTTPublishItem& item = _queue[_tail];
    strncpy(item.topic, topic, sizeof(item.topic) - 1);
    item.topic[sizeof(item.topic) - 1] = '\0';
    strncpy(item.payload, payload, sizeof(item.payload) - 1);
    item.payload[sizeof(item.payload) - 1] = '\0';
    item.qos = qos;
    item.retain = retain;
    item.retryCount = 0;

    _tail = (_tail + 1) % MQTT_QUEUE_CAPACITY;
    _count++;
    return true;
}

bool MQTTPublishQueue::dequeue(MQTTPublishItem& item) {
    if (isEmpty()) return false;

    item = _queue[_head];
    _head = (_head + 1) % MQTT_QUEUE_CAPACITY;
    _count--;
    return true;
}

bool MQTTPublishQueue::peek(MQTTPublishItem& item) const {
    if (isEmpty()) return false;
    item = _queue[_head];
    return true;
}

void MQTTPublishQueue::removeHead() {
    if (isEmpty()) return;
    _head = (_head + 1) % MQTT_QUEUE_CAPACITY;
    _count--;
}
