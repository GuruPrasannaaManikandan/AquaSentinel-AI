#ifndef WIFI_CONNECTION_HISTORY_H
#define WIFI_CONNECTION_HISTORY_H

#include "WiFiState.h"
#include <Arduino.h>
#include <string.h>

#define WIFI_HISTORY_CAPACITY 5

struct WiFiHistoryItem {
    unsigned long timestamp;
    WiFiState previousState;
    WiFiState currentState;
    int rssi;
    char ipAddress[16];
    char disconnectReason[32];
    int retryCount;
    unsigned long connectionDuration;
};

/**
 * @brief Circular log history tracking network transitions.
 */
class WiFiConnectionHistory {
private:
    WiFiHistoryItem _history[WIFI_HISTORY_CAPACITY];
    int _head;
    int _count;

public:
    WiFiConnectionHistory() : _head(0), _count(0) {}
    ~WiFiConnectionHistory() {}

    void addRecord(WiFiState prev, WiFiState next, int rssi, const char* ip, const char* reason, int retries, unsigned long duration) {
        WiFiHistoryItem item;
        item.timestamp = millis();
        item.previousState = prev;
        item.currentState = next;
        item.rssi = rssi;
        
        strncpy(item.ipAddress, ip, 15);
        item.ipAddress[15] = '\0';
        strncpy(item.disconnectReason, reason, 31);
        item.disconnectReason[31] = '\0';
        
        item.retryCount = retries;
        item.connectionDuration = duration;

        _history[_head] = item;
        _head = (_head + 1) % WIFI_HISTORY_CAPACITY;
        if (_count < WIFI_HISTORY_CAPACITY) {
            _count++;
        }
    }

    int getCount() const { return _count; }
    
    WiFiHistoryItem getRecord(int idx) const {
        if (idx < 0 || idx >= _count) {
            WiFiHistoryItem emptyItem = {0, WiFiState::DISCONNECTED, WiFiState::DISCONNECTED, 0, "", "", 0, 0};
            return emptyItem;
        }
        int realIdx = (_head - 1 - idx + WIFI_HISTORY_CAPACITY) % WIFI_HISTORY_CAPACITY;
        return _history[realIdx];
    }
};

#endif
