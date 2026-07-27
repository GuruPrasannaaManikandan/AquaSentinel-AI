#ifndef STATE_HISTORY_H
#define STATE_HISTORY_H

#include "State.h"
#include "Event.h"

#define MAX_HISTORY_ITEMS 5

struct HistoryItem {
    unsigned long timestamp;
    State previousState;
    Event event;
    State newState;
    const char* reason;
};

/**
 * @brief Circular transition log buffer avoiding dynamic memory fragmentation.
 */
class StateHistory {
private:
    HistoryItem _history[MAX_HISTORY_ITEMS];
    int _head;
    int _count;

public:
    StateHistory() : _head(0), _count(0) {}
    ~StateHistory() {}

    /**
     * @brief Inserts transition log.
     */
    void addRecord(State prev, Event ev, State next, unsigned long timestamp, const char* reason = "State Transition") {
        HistoryItem item = {timestamp, prev, ev, next, reason};
        _history[_head] = item;
        _head = (_head + 1) % MAX_HISTORY_ITEMS;
        if (_count < MAX_HISTORY_ITEMS) {
            _count++;
        }
    }

    int getCount() const { return _count; }
    
    /**
     * @brief Reads transition log (0 = newest, count-1 = oldest).
     */
    HistoryItem getRecord(int index) const {
        if (index < 0 || index >= _count) return {0, State::BOOT, Event::UNKNOWN_EVENT, State::BOOT, ""};
        int realIndex = (_head - 1 - index + MAX_HISTORY_ITEMS) % MAX_HISTORY_ITEMS;
        return _history[realIndex];
    }
};

#endif
