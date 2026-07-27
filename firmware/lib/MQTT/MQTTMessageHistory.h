#ifndef MQTT_MESSAGE_HISTORY_H
#define WIFI_MESSAGE_HISTORY_H // Let's keep it clean as MQTT_MESSAGE_HISTORY_H
#define MQTT_MESSAGE_HISTORY_H

#include <Arduino.h>
#include <string.h>

#define MQTT_HISTORY_CAPACITY 5

struct MQTTHistoryItem {
    unsigned long timestamp;
    char topic[32];
    char direction[4]; // "IN" or "OUT"
    size_t payloadSize;
    int qos;
    bool retain;
    bool success;
    unsigned long processingTimeMs;
};

/**
 * @brief Circular log history tracking MQTT packets.
 */
class MQTTMessageHistory {
private:
    MQTTHistoryItem _history[MQTT_HISTORY_CAPACITY];
    int _head;
    int _count;

public:
    MQTTMessageHistory() : _head(0), _count(0) {}
    ~MQTTMessageHistory() {}

    void addRecord(const char* topic, const char* dir, size_t size, int qos, bool retain, bool ok, unsigned long duration) {
        MQTTHistoryItem item;
        item.timestamp = millis();
        strncpy(item.topic, topic, 31);
        item.topic[31] = '\0';
        strncpy(item.direction, dir, 3);
        item.direction[3] = '\0';
        item.payloadSize = size;
        item.qos = qos;
        item.retain = retain;
        item.success = ok;
        item.processingTimeMs = duration;

        _history[_head] = item;
        _head = (_head + 1) % MQTT_HISTORY_CAPACITY;
        if (_count < MQTT_HISTORY_CAPACITY) {
            _count++;
        }
    }

    int getCount() const { return _count; }
    
    MQTTHistoryItem getRecord(int idx) const {
        if (idx < 0 || idx >= _count) {
            MQTTHistoryItem emptyItem = {0, "", "", 0, 0, false, false, 0};
            return emptyItem;
        }
        int realIdx = (_head - 1 - idx + MQTT_HISTORY_CAPACITY) % MQTT_HISTORY_CAPACITY;
        return _history[realIdx];
    }
};

#endif
