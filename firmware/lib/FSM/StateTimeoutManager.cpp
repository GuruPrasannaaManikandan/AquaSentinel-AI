#include "StateTimeoutManager.h"
#include <Arduino.h>

StateTimeoutManager::StateTimeoutManager() : _configCount(0), _stateEntryTime(0), _currentState(State::BOOT) {
    for (int i = 0; i < 10; i++) {
        _configs[i] = {State::BOOT, 0, Event::UNKNOWN_EVENT, false};
    }
    
    // Configure default FSM timeouts
    configureTimeout(State::FAULT, 10000, Event::TIMEOUT); // FAULT transitions after 10s
}

void StateTimeoutManager::configureTimeout(State state, unsigned long maxDurationMs, Event timeoutEvent) {
    if (_configCount >= 10) return;
    
    // Check if configuration exists
    for (int i = 0; i < _configCount; i++) {
        if (_configs[i].state == state) {
            _configs[i].maxDurationMs = maxDurationMs;
            _configs[i].timeoutEvent = timeoutEvent;
            _configs[i].enabled = true;
            return;
        }
    }

    _configs[_configCount++] = {state, maxDurationMs, timeoutEvent, true};
}

void StateTimeoutManager::onStateChange(State newState, unsigned long entryTime) {
    _currentState = newState;
    _stateEntryTime = entryTime;
}

bool StateTimeoutManager::checkTimeout(unsigned long currentTime, Event &timeoutEvent) {
    for (int i = 0; i < _configCount; i++) {
        if (_configs[i].state == _currentState && _configs[i].enabled) {
            unsigned long duration = currentTime - _stateEntryTime;
            if (duration >= _configs[i].maxDurationMs) {
                timeoutEvent = _configs[i].timeoutEvent;
                return true;
            }
        }
    }
    return false;
}
