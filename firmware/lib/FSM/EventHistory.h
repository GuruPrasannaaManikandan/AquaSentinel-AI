#ifndef EVENT_HISTORY_H
#define EVENT_HISTORY_H

#include "Event.h"
#include "EventSource.h"
#include "EventPriority.h"

#define MAX_EVENT_HISTORY_ITEMS 5

struct EventHistoryItem {
    unsigned long timestamp;
    unsigned long sequenceNumber;
    EventSource source;
    EventPriority priority;
    Event eventId;
    bool success;
};

/**
 * @brief Circular log history of processed events.
 */
class EventHistory {
private:
    EventHistoryItem _history[MAX_EVENT_HISTORY_ITEMS];
    int _head;
    int _count;

public:
    EventHistory() : _head(0), _count(0) {}
    ~EventHistory() {}

    void addRecord(unsigned long ts, unsigned long seq, EventSource src, EventPriority prio, Event ev, bool ok) {
        _history[_head] = {ts, seq, src, prio, ev, ok};
        _head = (_head + 1) % MAX_EVENT_HISTORY_ITEMS;
        if (_count < MAX_EVENT_HISTORY_ITEMS) {
            _count++;
        }
    }

    int getCount() const { return _count; }
    
    EventHistoryItem getRecord(int idx) const {
        if (idx < 0 || idx >= _count) {
            return {0, 0, EventSource::UNKNOWN, EventPriority::BACKGROUND, Event::UNKNOWN_EVENT, false};
        }
        int realIdx = (_head - 1 - idx + MAX_EVENT_HISTORY_ITEMS) % MAX_EVENT_HISTORY_ITEMS;
        return _history[realIdx];
    }
};

#endif
