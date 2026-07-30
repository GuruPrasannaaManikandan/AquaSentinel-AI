#ifndef BACKEND_SESSION_HISTORY_H
#define BACKEND_SESSION_HISTORY_H

#include <stddef.h>
#include <string.h>

#define MAX_BACKEND_SESSIONS 5

/**
 * @brief Record representing a completed communication session's logs.
 */
struct SessionHistoryItem {
    unsigned long timestamp;
    unsigned long sessionStartMs;
    unsigned long sessionEndMs;
    unsigned long syncTimeMs;
    unsigned long bytesSent;
    unsigned long bytesReceived;
    unsigned int reconnectCount;
    char failureReason[48];
};

/**
 * @brief Thread-safe, bounded, static history buffer logging communication sessions.
 */
class BackendSessionHistory {
private:
    SessionHistoryItem _sessions[MAX_BACKEND_SESSIONS];
    int _count;
    int _currentIndex;

public:
    BackendSessionHistory() : _count(0), _currentIndex(0) {
        memset(_sessions, 0, sizeof(_sessions));
    }
    ~BackendSessionHistory() {}

    /**
     * @brief Appends a finished session log entry to static circular store.
     */
    void addSession(const SessionHistoryItem& session) {
        _sessions[_currentIndex] = session;
        _currentIndex = (_currentIndex + 1) % MAX_BACKEND_SESSIONS;
        if (_count < MAX_BACKEND_SESSIONS) {
            _count++;
        }
    }

    int getCount() const { return _count; }
    
    /**
     * @brief Retrieves a logged session entry by chronological index (newest first).
     */
    bool getSession(int index, SessionHistoryItem& sessionOut) const {
        if (index < 0 || index >= _count) return false;
        int idx = (_currentIndex - 1 - index + MAX_BACKEND_SESSIONS) % MAX_BACKEND_SESSIONS;
        sessionOut = _sessions[idx];
        return true;
    }

    void clear() {
        _count = 0;
        _currentIndex = 0;
        memset(_sessions, 0, sizeof(_sessions));
    }
};

#endif // BACKEND_SESSION_HISTORY_H
