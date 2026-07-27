#ifndef FSM_H
#define FSM_H

#include "hal/HAL.h"
#include "StateContext.h"
#include "TransitionTable.h"
#include "StateHistory.h"
#include "FSMDiagnostics.h"
#include "FSMObserverManager.h"
#include "StateTimeoutManager.h"
#include "EventHistory.h"
#include "EventDispatcher.h"

class FSM {
private:
    HAL& _hal;
    StateContext _context;
    TransitionTable _transitionTable;
    StateHistory _history;
    FSMDiagnostics _diagnostics;

    // Infrastructure additions
    EventDispatcher* _dispatcher;
    FSMObserverManager _observerManager;
    StateTimeoutManager _timeoutManager;
    EventHistory _eventHistory;

    // Helper functions for entry/exit actions
    void executeEntryActions(State state);
    void executeExitActions(State state);
    void executeUpdateActions(State state);

public:
    FSM(HAL& hal);
    ~FSM() {}

    void setDispatcher(EventDispatcher* dispatcher);
    EventDispatcher* getDispatcher() const { return _dispatcher; }
    FSMObserverManager& getObserverManager() { return _observerManager; }
    StateTimeoutManager& getTimeoutManager() { return _timeoutManager; }
    const EventHistory& getEventHistory() const { return _eventHistory; }

    /**
     * @brief Boot initialization.
     */
    void initialize();

    /**
     * @brief Periodic update called by scheduler. Checks timeouts
     * and executes state update behaviors.
     */
    void update();

    /**
     * @brief Internal routing helper forwarding events to dispatcher queue.
     */
    void dispatch(Event ev, const char* reason = "Event triggered");

    /**
     * @brief Core dispatcher interface executing transitions.
     */
    void processEvent(const FSMEvent& event);

    State getCurrentState() const { return _context.currentState; }
    const StateContext& getContext() const { return _context; }
    const StateHistory& getHistory() const { return _history; }
    
    /**
     * @brief Gathers diagnostics metrics, compiling current queue depth.
     */
    FSMDiagnostics getDiagnostics();
};

#endif
