#ifndef FSM_OBSERVER_MANAGER_H
#define FSM_OBSERVER_MANAGER_H

#include "IFSMObserver.h"

#define MAX_OBSERVERS 5

class FSMObserverManager {
private:
    IFSMObserver* _observers[MAX_OBSERVERS];
    int _observerCount;

public:
    FSMObserverManager();
    ~FSMObserverManager() {}

    bool subscribe(IFSMObserver* observer);
    bool unsubscribe(IFSMObserver* observer);
    
    /**
     * @brief Loops list and executes notifications.
     */
    void notifyTransition(State from, Event ev, State to);
    
    int getObserverCount() const { return _observerCount; }
};

#endif
