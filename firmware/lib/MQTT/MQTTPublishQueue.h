#ifndef MQTT_PUBLISH_QUEUE_H
#define MQTT_PUBLISH_QUEUE_H

#define MQTT_QUEUE_CAPACITY 8

struct MQTTPublishItem {
    char topic[64];
    char payload[512];
    int qos;
    bool retain;
    int retryCount;
};

/**
 * @brief Static FIFO queue holding pending MQTT publishes.
 */
class MQTTPublishQueue {
private:
    MQTTPublishItem _queue[MQTT_QUEUE_CAPACITY];
    int _head;
    int _tail;
    int _count;
    unsigned long _droppedCount;

public:
    MQTTPublishQueue();
    ~MQTTPublishQueue() {}

    bool enqueue(const char* topic, const char* payload, int qos = 0, bool retain = false);
    bool dequeue(MQTTPublishItem& item);
    bool peek(MQTTPublishItem& item) const;
    void removeHead();
    
    int getCount() const { return _count; }
    unsigned long getDroppedCount() const { return _droppedCount; }
    bool isFull() const { return _count >= MQTT_QUEUE_CAPACITY; }
    bool isEmpty() const { return _count == 0; }
};

#endif
