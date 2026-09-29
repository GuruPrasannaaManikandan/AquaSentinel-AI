#ifndef TRANSITION_H
#define TRANSITION_H

#include "State.h"
#include "Event.h"

typedef bool (*TransitionGuard)();
typedef void (*TransitionAction)();

/**
 * @brief Represents a transition mapping between states.
 */
struct Transition {
    State fromState;
    Event event;
    State toState;
    TransitionGuard guard;
    TransitionAction action;
};

#endif
