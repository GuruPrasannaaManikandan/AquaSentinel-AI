#include "EventDispatcher.h"
#include "FSM.h"
#include <Arduino.h>

EventDispatcher::EventDispatcher() : _fsm(nullptr), _sequenceCounter(0) {}

void EventDispatcher::setFSM(FSM* fsm) {
    _fsm = fsm;
}

bool EventDispatcher::publish(Event eventId, EventSource source, EventPriority priority, void* payload) {
    FSMEvent ev;
    ev.id = eventId;
    ev.timestamp = millis();
    ev.source = source;
    ev.priority = priority;
    ev.payload = payload;
    ev.sequenceNumber = _sequenceCounter++;

    return _queue.enqueue(ev);
}

void EventDispatcher::processQueue() {
    if (!_fsm) return;

    FSMEvent ev;
    while (_queue.dequeue(ev)) {
        _fsm->processEvent(ev);
    }
}
