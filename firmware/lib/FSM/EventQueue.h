#ifndef EVENT_QUEUE_H
#define EVENT_QUEUE_H

#include "FSMEvent.h"

#define EVENT_QUEUE_CAPACITY 10

class EventQueue {
private:
    FSMEvent _queue[EVENT_QUEUE_CAPACITY];
    int _head;
    int _tail;
    int _count;
    unsigned long _droppedEvents;

public:
    EventQueue();
    ~EventQueue() {}

    /**
     * @brief Pushes event sorted by priority (CRITICAL -> BACKGROUND).
     * Maintains FIFO ordering for identical priority events.
     */
    bool enqueue(const FSMEvent &event);
    
    /**
     * @brief Pulls the highest priority due event from the front of the queue.
     */
    bool dequeue(FSMEvent &event);
    
    bool isEmpty() const { return _count == 0; }
    bool isFull() const { return _count == EVENT_QUEUE_CAPACITY; }
    int getCount() const { return _count; }
    unsigned long getDroppedEvents() const { return _droppedEvents; }
    void clear();
};

#endif
