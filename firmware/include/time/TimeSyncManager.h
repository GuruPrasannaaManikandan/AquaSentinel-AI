/**
 * @file TimeSyncManager.h
 * @brief Dedicated C++ Firmware SNTP/NTP Time Synchronization Component for ESP32.
 * 
 * Milestone V4.8.3 Physical Hardware Time Model.
 * Manages SNTP clock synchronization, maintains explicit sync states, and exposes
 * wall-clock timestamps and sync metadata.
 */

#ifndef TIME_SYNC_MANAGER_H
#define TIME_SYNC_MANAGER_H

#include <Arduino.h>
#include <time.h>

enum class TimeSyncState {
    UNSYNCED,
    SYNCING,
    SYNCED,
    SYNC_FAILED
};

class TimeSyncManager {
private:
    TimeSyncState currentState;
    const char* ntpServer1;
    const char* ntpServer2;
    long gmtOffset_sec;
    int daylightOffset_sec;
    unsigned long lastSyncMillis;
    char lastSyncIsoTimestamp[32];
    bool initialized;

public:
    TimeSyncManager(const char* server1 = "pool.ntp.org", const char* server2 = "time.nist.gov", long gmtOffset = 0, int daylightOffset = 0)
        : currentState(TimeSyncState::UNSYNCED),
          ntpServer1(server1),
          ntpServer2(server2),
          gmtOffset_sec(gmtOffset),
          daylightOffset_sec(daylightOffset),
          lastSyncMillis(0),
          initialized(false) {
        memset(lastSyncIsoTimestamp, 0, sizeof(lastSyncIsoTimestamp));
    }

    void initialize() {
        currentState = TimeSyncState::UNSYNCED;
        initialized = true;
    }

    bool syncNTP(unsigned long timeoutMs = 5000) {
        if (!initialized) {
            initialize();
        }
        currentState = TimeSyncState::SYNCING;

        // Configure SNTP via ESP-IDF / Arduino core
        configTime(gmtOffset_sec, daylightOffset_sec, ntpServer1, ntpServer2);

        struct tm timeinfo;
        unsigned long startMs = millis();
        while ((millis() - startMs) < timeoutMs) {
            if (getLocalTime(&timeinfo, 10)) {
                if (timeinfo.tm_year > (2020 - 1900)) { // Valid year check (> 2020)
                    currentState = TimeSyncState::SYNCED;
                    lastSyncMillis = millis();
                    strftime(lastSyncIsoTimestamp, sizeof(lastSyncIsoTimestamp), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
                    return true;
                }
            }
            delay(100);
        }

        currentState = TimeSyncState::SYNC_FAILED;
        return false;
    }

    TimeSyncState getState() const {
        return currentState;
    }

    const char* getStateString() const {
        switch (currentState) {
            case TimeSyncState::SYNCED: return "SYNCED";
            case TimeSyncState::SYNCING: return "SYNCING";
            case TimeSyncState::SYNC_FAILED: return "SYNC_FAILED";
            case TimeSyncState::UNSYNCED: default: return "UNSYNCED";
        }
    }

    const char* getClockSource() const {
        return (currentState == TimeSyncState::SYNCED) ? "NTP" : "UNSYNCED_BOOT_TICK";
    }

    String getIsoTimestamp() {
        struct tm timeinfo;
        if (currentState == TimeSyncState::SYNCED && getLocalTime(&timeinfo, 10)) {
            char buf[32];
            strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
            return String(buf);
        }
        // Fallback for unsynchronized state: Formatted relative boot tick
        unsigned long uptimeSec = millis() / 1000;
        return "1970-01-01T00:00:" + String(uptimeSec < 10 ? "0" : "") + String(uptimeSec) + "Z";
    }

    const char* getLastSyncTimestamp() const {
        return lastSyncIsoTimestamp;
    }
};

#endif // TIME_SYNC_MANAGER_H
