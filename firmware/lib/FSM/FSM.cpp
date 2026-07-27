#include "FSM.h"
#include <Arduino.h>
#include <string.h>

FSM::FSM(HAL& hal) : _hal(hal), _dispatcher(nullptr) {
    _context.currentState = State::BOOT;
    _context.previousState = State::BOOT;
    _context.lastEvent = Event::UNKNOWN_EVENT;
    _context.transitionCount = 0;
    _context.stateEntryTime = 0;
    _context.stateExitTime = 0;
    _context.currentUptime = 0;
    _context.recoveryAttempts = 0;
    _context.diagnosticFlags = 0;

    _diagnostics.transitionCount = 0;
    _diagnostics.invalidEventsCount = 0;
    _diagnostics.invalidTransitionsCount = 0;
    _diagnostics.timeoutsCount = 0;
    _diagnostics.guardFailuresCount = 0;
    _diagnostics.queueDepth = 0;
    _diagnostics.droppedEvents = 0;
    _diagnostics.observerNotifications = 0;
    _diagnostics.averageTransitionTimeUs = 0;
    _diagnostics.maxTransitionTimeUs = 0;
}

void FSM::setDispatcher(EventDispatcher* dispatcher) {
    _dispatcher = dispatcher;
    if (_dispatcher) {
        _dispatcher->setFSM(this);
    }
}

void FSM::initialize() {
    _context.stateEntryTime = millis();
    _timeoutManager.onStateChange(State::BOOT, millis());
    dispatch(Event::BOOT_COMPLETE, "System boot initialized");
}

void FSM::update() {
    unsigned long nowMs = millis();
    _context.currentUptime = nowMs;

    // 1. Process enqueued events via Dispatcher
    if (_dispatcher) {
        _dispatcher->processQueue();
    }

    // 2. Evaluate State Timeouts
    Event timeoutEvent;
    if (_timeoutManager.checkTimeout(nowMs, timeoutEvent)) {
        _diagnostics.timeoutsCount++;
        dispatch(timeoutEvent, "State timeout limit reached");
    }

    // 3. Run active state update behaviors
    executeUpdateActions(_context.currentState);
}

void FSM::dispatch(Event ev, const char* reason) {
    if (_dispatcher) {
        // All module events are enqueued via dispatcher publishes
        _dispatcher->publish(ev, EventSource::FSM, EventPriority::NORMAL);
    }
}

void FSM::processEvent(const FSMEvent& event) {
    unsigned long startUs = micros();
    Transition transitionMatch;
    State prev = _context.currentState;

    bool hasTransition = _transitionTable.getTransition(prev, event.id, transitionMatch);

    if (hasTransition) {
        // Verify Guard check
        if (transitionMatch.guard != nullptr) {
            if (!transitionMatch.guard()) {
                _diagnostics.guardFailuresCount++;
                Serial.print("[FSM-WARNING] Transition guard blocked event: ");
                Serial.println((int)event.id);
                _eventHistory.addRecord(event.timestamp, event.sequenceNumber, event.source, event.priority, event.id, false);
                return;
            }
        }

        // Run exit behaviors
        executeExitActions(prev);

        // Run transition action callback
        if (transitionMatch.action != nullptr) {
            transitionMatch.action();
        }

        // Execute state update
        State next = transitionMatch.toState;
        _context.previousState = prev;
        _context.currentState = next;
        _context.lastEvent = event.id;
        _context.stateExitTime = millis();
        _context.stateEntryTime = millis();
        _context.transitionCount++;

        // Notify Timeout manager
        _timeoutManager.onStateChange(next, millis());

        // Run entry behaviors
        executeEntryActions(next);

        // Notify Observers
        _observerManager.notifyTransition(prev, event.id, next);
        _diagnostics.observerNotifications++;

        // Log transition history
        _history.addRecord(prev, event.id, next, millis(), "Transition completed");
        _eventHistory.addRecord(event.timestamp, event.sequenceNumber, event.source, event.priority, event.id, true);

        // Compile Transition time diagnostic
        unsigned long elapsedUs = micros() - startUs;
        _diagnostics.transitionCount++;
        if (elapsedUs > _diagnostics.maxTransitionTimeUs) {
            _diagnostics.maxTransitionTimeUs = elapsedUs;
        }
        _diagnostics.averageTransitionTimeUs = (_diagnostics.averageTransitionTimeUs * (_diagnostics.transitionCount - 1) + elapsedUs) / _diagnostics.transitionCount;
    } else {
        // Record invalid transitions
        _diagnostics.invalidTransitionsCount++;
        _eventHistory.addRecord(event.timestamp, event.sequenceNumber, event.source, event.priority, event.id, false);
    }
}

FSMDiagnostics FSM::getDiagnostics() {
    _diagnostics.queueDepth = _dispatcher ? _dispatcher->getQueue().getCount() : 0;
    _diagnostics.droppedEvents = _dispatcher ? _dispatcher->getQueue().getDroppedEvents() : 0;
    _diagnostics.observerNotifications = _observerManager.getObserverCount() * _diagnostics.transitionCount;
    return _diagnostics;
}

void FSM::executeEntryActions(State state) {
    switch (state) {
        case State::BOOT:
            break;
        case State::INITIALIZING:
            Serial.println("[FSM] Entering INITIALIZING state. Polling HAL checks...");
            break;
        case State::SELF_TEST:
            Serial.println("[FSM] Entering SELF_TEST state. Invoking diagnostics...");
            break;
        case State::IDLE:
            Serial.println("[FSM] Entering IDLE state. System idle.");
            _hal.writeActuator("green_led", "ON");
            _hal.writeActuator("yellow_led", "OFF");
            _hal.writeActuator("red_led", "OFF");
            _hal.writeActuator("buzzer", "OFF");
            _hal.writeActuator("pump_relay", "OFF");
            break;
        case State::MONITORING:
            Serial.println("[FSM] Entering MONITORING state. Ecosystem safe.");
            _hal.writeActuator("green_led", "ON");
            _hal.writeActuator("yellow_led", "OFF");
            _hal.writeActuator("red_led", "OFF");
            _hal.writeActuator("buzzer", "OFF");
            break;
        case State::WARNING:
            Serial.println("[FSM] Entering WARNING state. Early ecosystem stress detected.");
            _hal.writeActuator("green_led", "OFF");
            _hal.writeActuator("yellow_led", "ON");
            _hal.writeActuator("red_led", "OFF");
            _hal.writeActuator("buzzer", "OFF");
            break;
        case State::ALERT:
            Serial.println("[FSM] Entering ALERT state. Critical ecological hazard! Activating aerator...");
            _hal.writeActuator("green_led", "OFF");
            _hal.writeActuator("yellow_led", "OFF");
            _hal.writeActuator("red_led", "ON");
            _hal.writeActuator("buzzer", "OFF");
            _hal.writeActuator("pump_relay", "ON");
            break;
        case State::FAULT:
            Serial.println("[FSM] Entering FAULT state. Hardware diagnostics error! Sounding buzzer...");
            _hal.writeActuator("green_led", "OFF");
            _hal.writeActuator("yellow_led", "OFF");
            _hal.writeActuator("red_led", "ON");
            _hal.writeActuator("buzzer", "ON");
            _hal.writeActuator("pump_relay", "OFF");
            break;
        case State::RECOVERY:
            Serial.println("[FSM] Entering RECOVERY state. Attempting parameter reset...");
            _context.recoveryAttempts++;
            break;
        case State::SHUTDOWN:
            Serial.println("[FSM] Entering SHUTDOWN state. Hard lock suspension!");
            _hal.writeActuator("green_led", "OFF");
            _hal.writeActuator("yellow_led", "OFF");
            _hal.writeActuator("red_led", "OFF");
            _hal.writeActuator("buzzer", "OFF");
            _hal.writeActuator("pump_relay", "OFF");
            _hal.shutdown();
            break;
    }
}

void FSM::executeExitActions(State state) {
    // Optional cleaning hooks
}

void FSM::executeUpdateActions(State state) {
    switch (state) {
        case State::INITIALIZING: {
            TelemetryData data = _hal.readAllSensors();
            if (strcmp(data.sensor_status, "FAULT") != 0) {
                dispatch(Event::SENSORS_READY, "HAL telemetry online");
            } else {
                dispatch(Event::SENSOR_FAULT, "HAL sensors failed initializing");
            }
            break;
        }
        case State::SELF_TEST: {
            bool passed = _hal.runSelfTest();
            if (passed) {
                dispatch(Event::SELF_TEST_PASS, "Diagnostics check passed");
            } else {
                dispatch(Event::SELF_TEST_FAIL, "Diagnostics check failed");
            }
            break;
        }
        case State::IDLE: {
            dispatch(Event::SENSORS_READY, "Activating monitor loop");
            break;
        }
        case State::MONITORING:
        case State::WARNING:
        case State::ALERT: {
            TelemetryData data = _hal.readAllSensors();
            if (strcmp(data.sensor_status, "FAULT") == 0) {
                dispatch(Event::FAULT_DETECTED, "Hardware diagnostic fault");
            } else if (strcmp(data.sensor_status, "CRITICAL") == 0) {
                dispatch(Event::ALERT_DETECTED, "Critical thresholds exceeded");
            } else if (strcmp(data.sensor_status, "WARNING") == 0) {
                dispatch(Event::WARNING_DETECTED, "Warning thresholds exceeded");
            } else if (strcmp(data.sensor_status, "OK") == 0) {
                dispatch(Event::SENSORS_READY, "Parameters back to nominal");
            }
            break;
        }
        case State::FAULT: {
            // Checked automatically by StateTimeoutManager, no manual timer code needed!
            break;
        }
        case State::RECOVERY: {
            bool passed = _hal.runSelfTest();
            if (passed) {
                _context.recoveryAttempts = 0;
                dispatch(Event::RECOVERY_SUCCESS, "Recovery diagnostics passed");
            } else {
                if (_context.recoveryAttempts >= 3) {
                    dispatch(Event::RECOVERY_FAILED, "Maximum recovery attempts exceeded");
                } else {
                    dispatch(Event::RECOVERY_SUCCESS, "Recovery retry check");
                }
            }
            break;
        }
        case State::BOOT:
        case State::SHUTDOWN:
            break;
    }
}
