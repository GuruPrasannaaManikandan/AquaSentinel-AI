#ifndef EVENT_LOGGER_H
#define EVENT_LOGGER_H

#include <stddef.h>
#include <string.h>

#define MAX_LOG_ENTRIES 50

/**
 * @brief Structure representing a recorded diagnostics event log.
 */
struct EventLogEntry {
    unsigned long timestamp;
    char category[16]; // "FAULT", "RECOVERY", "WARNING", "CONFIG", "CONN", "STATE"
    char message[64];
};

/**
 * @brief Class logging system events to a static circular queue.
 */
class EventLogger {
private:
    EventLogEntry _entries[MAX_LOG_ENTRIES];
    int _count;
    int _currentIndex;

public:
    EventLogger();
    ~EventLogger() {}

    /**
     * @brief Registers an event in the circular log.
     */
    void logEvent(const char* category, const char* message);

    int getCount() const { return _count; }
    
    /**
     * @brief Retrieves a log entry by index (newest first).
     */
    bool getEntry(int index, EventLogEntry& entryOut) const;

    void clear();
};

#endif // EVENT_LOGGER_H
