#include "EventQueue.h"
#include <string.h>

EventQueue::EventQueue() : _head(0), _tail(0), _count(0), _droppedEvents(0) {
    memset(_queue, 0, sizeof(_queue));
}

bool EventQueue::enqueue(const FSMEvent &event) {
    if (isFull()) {
        _droppedEvents++;
        return false;
    }

    // High priority events are moved to the front. 
    // Scan backwards from tail to find the insertion index
    int insertPos = _tail;
    for (int i = 0; i < _count; i++) {
        int idx = (_tail - 1 - i + EVENT_QUEUE_CAPACITY) % EVENT_QUEUE_CAPACITY;
        if ((int)_queue[idx].priority >= (int)event.priority) {
            insertPos = (idx + 1) % EVENT_QUEUE_CAPACITY;
            break;
        }
        if (idx == _head && (int)_queue[idx].priority < (int)event.priority) {
            insertPos = _head;
        }
    }

    // Shift elements to make room
    int current = _tail;
    while (current != insertPos) {
        int prevIdx = (current - 1 + EVENT_QUEUE_CAPACITY) % EVENT_QUEUE_CAPACITY;
        _queue[current] = _queue[prevIdx];
        current = prevIdx;
    }

    _queue[insertPos] = event;
    _tail = (_tail + 1) % EVENT_QUEUE_CAPACITY;
    _count++;
    return true;
}

bool EventQueue::dequeue(FSMEvent &event) {
    if (isEmpty()) {
        return false;
    }

    event = _queue[_head];
    memset(&_queue[_head], 0, sizeof(FSMEvent));
    _head = (_head + 1) % EVENT_QUEUE_CAPACITY;
    _count--;
    return true;
}

void EventQueue::clear() {
    _head = 0;
    _tail = 0;
    _count = 0;
    _droppedEvents = 0;
    memset(_queue, 0, sizeof(_queue));
}
