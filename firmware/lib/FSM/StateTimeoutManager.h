#ifndef STATE_TIMEOUT_MANAGER_H
#define STATE_TIMEOUT_MANAGER_H

#include "State.h"
#include "Event.h"

struct StateTimeoutConfig {
    State state;
    unsigned long maxDurationMs;
    Event timeoutEvent;
    bool enabled;
};

class StateTimeoutManager {
private:
    StateTimeoutConfig _configs[10]; // Capped at 10 states
    int _configCount;
    unsigned long _stateEntryTime;
    State _currentState;

public:
    StateTimeoutManager();
    ~StateTimeoutManager() {}

    void configureTimeout(State state, unsigned long maxDurationMs, Event timeoutEvent);
    void onStateChange(State newState, unsigned long entryTime);
    
    /**
     * @brief Evaluates active timeouts and sets event parameter on expiry.
     */
    bool checkTimeout(unsigned long currentTime, Event &timeoutEvent);
};

#endif
