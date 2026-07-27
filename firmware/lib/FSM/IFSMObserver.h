#ifndef IFSM_OBSERVER_H
#define IFSM_OBSERVER_H

#include "State.h"
#include "Event.h"

/**
 * @brief Interface for FSM status transition observers.
 */
class IFSMObserver {
public:
    virtual ~IFSMObserver() {}

    /**
     * @brief Triggered on successful FSM state changes.
     */
    virtual void onStateTransition(State fromState, Event ev, State toState) = 0;
};

#endif
