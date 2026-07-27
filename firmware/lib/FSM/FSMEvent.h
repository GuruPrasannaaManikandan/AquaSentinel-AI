#ifndef FSM_EVENT_H
#define FSM_EVENT_H

#include "Event.h"
#include "EventSource.h"
#include "EventPriority.h"

/**
 * @brief Dynamic event data structure carrying metadata payloads.
 */
struct FSMEvent {
    Event id;
    unsigned long timestamp;
    EventSource source;
    EventPriority priority;
    void* payload; // Nullable parameter pointer
    unsigned long sequenceNumber;
};

#endif
