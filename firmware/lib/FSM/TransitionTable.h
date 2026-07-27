#ifndef TRANSITION_TABLE_H
#define TRANSITION_TABLE_H

#include "Transition.h"

#define MAX_TRANSITIONS 30

class TransitionTable {
private:
    Transition _transitions[MAX_TRANSITIONS];
    int _transitionCount;

public:
    TransitionTable();
    ~TransitionTable() {}

    void addTransition(State from, Event ev, State to, TransitionGuard guard = nullptr, TransitionAction action = nullptr);
    
    /**
     * @brief Resolves transition rules matching state and events.
     */
    bool getTransition(State current, Event ev, Transition &match) const;
  };

#endif
