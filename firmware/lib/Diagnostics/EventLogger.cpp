#include "EventLogger.h"
#include <Arduino.h>

EventLogger::EventLogger() {
    clear();
}

void EventLogger::clear() {
    _count = 0;
    _currentIndex = 0;
    memset(_entries, 0, sizeof(_entries));
}

void EventLogger::logEvent(const char* category, const char* message) {
    _entries[_currentIndex].timestamp = millis();
    
    strncpy(_entries[_currentIndex].category, category ? category : "GENERAL", sizeof(_entries[_currentIndex].category) - 1);
    _entries[_currentIndex].category[sizeof(_entries[_currentIndex].category) - 1] = '\0';

    strncpy(_entries[_currentIndex].message, message ? message : "", sizeof(_entries[_currentIndex].message) - 1);
    _entries[_currentIndex].message[sizeof(_entries[_currentIndex].message) - 1] = '\0';

    Serial.print("[EVENT-LOGGER] [");
    Serial.print(_entries[_currentIndex].category);
    Serial.print("] ");
    Serial.println(_entries[_currentIndex].message);

    _currentIndex = (_currentIndex + 1) % MAX_LOG_ENTRIES;
    if (_count < MAX_LOG_ENTRIES) {
        _count++;
    }
}

bool EventLogger::getEntry(int index, EventLogEntry& entryOut) const {
    if (index < 0 || index >= _count) {
        return false;
    }
    
    int idx = (_currentIndex - 1 - index + MAX_LOG_ENTRIES) % MAX_LOG_ENTRIES;
    entryOut = _entries[idx];
    return true;
}
