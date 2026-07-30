# Recovery Manager (`RecoveryManager`)

The `RecoveryManager` coordinates multi-stage recovery escalations.

## Recovery Escalation Path

```
                    Active Fault Registered
                               │
                               ▼
                    [ Severity Check: WARNING ]
                               │
                   (Level 1: RETRY Escalation)
                               │
                 Upto 3 Retries; if unresolved:
                               │
                  (Level 2: RESTART Escalation)
                               │
                    Publish Event::WARNING_DETECTED
                               │
                               ▼
                     [ Severity Check: ERROR ]
                               │
                  (Level 2: RESTART Subsystem)
                               │
                    Publish Event::FAULT_DETECTED
                      (FSM Transitions to FAULT)
                               │
                 If unresolved / repeats:
                               │
                               ▼
                   [ Severity Check: CRITICAL ]
                               │
                  (Level 3: SHUTDOWN Escalation)
                               │
                    Publish Event::SHUTDOWN_REQUEST
                      (FSM Transitions to SHUTDOWN)
```

## Escalation Stages

1. **Retry (`RETRY`)**:
   Temporarily backs off and retries the operation (e.g. Wi-Fi reconnection). Supports up to 3 attempts.
2. **Subsystem Restart (`RESTART`)**:
   Publishes `Event::FAULT_DETECTED` to the `EventDispatcher` to force the FSM to transition to its `FAULT` recovery loop.
3. **Safe Shutdown (`SHUTDOWN`)**:
   If the fault is critical or repeats, it escalates by publishing `Event::SHUTDOWN_REQUEST` to the `EventDispatcher` to transition the FSM to its safe shutdown mode, disabling relays and locking alarms.

## Subsystem Boundaries

The `RecoveryManager` communicates with the state machine only via the decoupled `EventDispatcher` queue, protecting subsystem boundaries.
It does not invoke FSM class methods directly.
