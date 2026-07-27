#ifndef STATE_CONTEXT_H
#define STATE_CONTEXT_H

#include "State.h"
#include "Event.h"

/**
 * @brief Dynamic context tracking parameters for FSM state executions.
 */
struct StateContext {
    State currentState;
    State previousState;
    Event lastEvent;
    unsigned long transitionCount;
    unsigned long stateEntryTime;
    unsigned long stateExitTime;
    unsigned long currentUptime;
    unsigned int recoveryAttempts;
    unsigned int diagnosticFlags;
};

#endif
