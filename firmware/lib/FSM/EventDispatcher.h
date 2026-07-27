#ifndef EVENT_DISPATCHER_H
#define EVENT_DISPATCHER_H

#include "FSMEvent.h"
#include "EventQueue.h"

class FSM; // Forward declaration

class EventDispatcher {
private:
    EventQueue _queue;
    FSM* _fsm;
    unsigned long _sequenceCounter;

public:
    EventDispatcher();
    ~EventDispatcher() {}

    void setFSM(FSM* fsm);
    
    /**
     * @brief Creates and enqueues event parameter blocks.
     */
    bool publish(Event eventId, EventSource source, EventPriority priority = EventPriority::NORMAL, void* payload = nullptr);
    
    /**
     * @brief Dequeues enqueued events and processes them in FSM.
     */
    void processQueue();
    
    EventQueue& getQueue() { return _queue; }
};

#endif
