# FSM Validation

This document describes the validation of the edge validation FSM.

## Reachability and Transition Checks

The verification manager verifies FSM transitions against the FSM specifications:

1. **State Reachability**:
   - `BOOT` $\rightarrow$ `INITIALIZING` on complete.
   - `INITIALIZING` $\rightarrow$ `CONNECTING` on self-test pass.
   - `CONNECTING` $\rightarrow$ `SENSING` on network ready.
   - `SENSING` $\rightarrow$ `PUBLISHING` on scheduler polling ticks.
   - `PUBLISHING` $\rightarrow$ `WAITING` on publish success.
   - `WAITING` $\rightarrow$ `SENSING` on telemetry interval elapsed.

2. **Transition Rejection**:
   - Verifies that invalid transitions (e.g. `BOOT` directly to `PUBLISHING`) are rejected.

3. **Recovery and Shutdown Paths**:
   - **Recovery**: Verifies that publishing `Event::FAULT_DETECTED` transitions FSM to `FAULT`, triggering actuator safe states and recovery retries.
   - **Shutdown**: Verifies that publishing `Event::SHUTDOWN_REQUEST` transitions FSM to `SHUTDOWN`, locking indicators, activating the alarm buzzer, and blocking normal polling.
