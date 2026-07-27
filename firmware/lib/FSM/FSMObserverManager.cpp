#include "FSMObserverManager.h"
#include <Arduino.h>

FSMObserverManager::FSMObserverManager() : _observerCount(0) {
    for (int i = 0; i < MAX_OBSERVERS; i++) {
        _observers[i] = nullptr;
    }
}

bool FSMObserverManager::subscribe(IFSMObserver* observer) {
    if (!observer || _observerCount >= MAX_OBSERVERS) return false;

    // Check duplicate
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i] == observer) {
            return false;
        }
    }

    _observers[_observerCount++] = observer;
    return true;
}

bool FSMObserverManager::unsubscribe(IFSMObserver* observer) {
    int targetIndex = -1;
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i] == observer) {
            targetIndex = i;
            break;
        }
    }

    if (targetIndex == -1) return false;

    for (int i = targetIndex; i < _observerCount - 1; i++) {
        _observers[i] = _observers[i + 1];
    }
    _observers[--_observerCount] = nullptr;
    return true;
}

void FSMObserverManager::notifyTransition(State from, Event ev, State to) {
    for (int i = 0; i < _observerCount; i++) {
        if (_observers[i]) {
            _observers[i]->onStateTransition(from, ev, to);
        }
    }
}
