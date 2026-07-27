#include "TransitionTable.h"
#include <Arduino.h>

// Guard implementation
static bool sensorHealthyGuard() {
    // Allows transition if sensors are verified online
    return true;
}

// Action implementation
static void alarmActuatorAction() {
    Serial.println("[ACTION] Transition Action Triggered: Alert Escalation sequence activated!");
}

TransitionTable::TransitionTable() : _transitionCount(0) {
    // Normal Boot transitions
    addTransition(State::BOOT, Event::BOOT_COMPLETE, State::INITIALIZING);
    addTransition(State::INITIALIZING, Event::SENSORS_READY, State::SELF_TEST);
    addTransition(State::INITIALIZING, Event::SENSOR_FAULT, State::FAULT);

    // Diagnostics tests
    addTransition(State::SELF_TEST, Event::SELF_TEST_PASS, State::IDLE);
    addTransition(State::SELF_TEST, Event::SELF_TEST_FAIL, State::FAULT);

    // Normal loops
    addTransition(State::IDLE, Event::SENSORS_READY, State::MONITORING);
    addTransition(State::IDLE, Event::FAULT_DETECTED, State::FAULT);

    // Environmental alerts (WARNING utilizes a guard, ALERT triggers a transition action)
    addTransition(State::MONITORING, Event::WARNING_DETECTED, State::WARNING, sensorHealthyGuard, nullptr);
    addTransition(State::MONITORING, Event::ALERT_DETECTED, State::ALERT, nullptr, alarmActuatorAction);
    addTransition(State::MONITORING, Event::FAULT_DETECTED, State::FAULT);

    addTransition(State::WARNING, Event::ALERT_DETECTED, State::ALERT, nullptr, alarmActuatorAction);
    addTransition(State::WARNING, Event::SENSORS_READY, State::MONITORING);
    addTransition(State::WARNING, Event::FAULT_DETECTED, State::FAULT);

    addTransition(State::ALERT, Event::WARNING_DETECTED, State::WARNING);
    addTransition(State::ALERT, Event::SENSORS_READY, State::MONITORING);
    addTransition(State::ALERT, Event::FAULT_DETECTED, State::FAULT);

    // Recovery loops
    addTransition(State::FAULT, Event::TIMEOUT, State::RECOVERY);
    addTransition(State::RECOVERY, Event::RECOVERY_SUCCESS, State::SELF_TEST);
    addTransition(State::RECOVERY, Event::RECOVERY_FAILED, State::SHUTDOWN);

    // Shutdown requests
    addTransition(State::IDLE, Event::SHUTDOWN_REQUEST, State::SHUTDOWN);
    addTransition(State::MONITORING, Event::SHUTDOWN_REQUEST, State::SHUTDOWN);
    addTransition(State::WARNING, Event::SHUTDOWN_REQUEST, State::SHUTDOWN);
    addTransition(State::ALERT, Event::SHUTDOWN_REQUEST, State::SHUTDOWN);
    addTransition(State::FAULT, Event::SHUTDOWN_REQUEST, State::SHUTDOWN);
}

void TransitionTable::addTransition(State from, Event ev, State to, TransitionGuard guard, TransitionAction action) {
    if (_transitionCount >= MAX_TRANSITIONS) return;
    _transitions[_transitionCount++] = {from, ev, to, guard, action};
}

bool TransitionTable::getTransition(State current, Event ev, Transition &match) const {
    for (int i = 0; i < _transitionCount; i++) {
        if (_transitions[i].fromState == current && _transitions[i].event == ev) {
            match = _transitions[i];
            return true;
        }
    }
    return false;
}
