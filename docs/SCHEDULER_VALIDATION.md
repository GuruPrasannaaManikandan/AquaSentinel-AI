# Scheduler Validation

This document describes the validation of the cooperative task scheduler.

## Scheduling Verification Metrics

1. **Task Execution Order**:
   Verifies that tasks are dispatched according to priority (`CRITICAL` > `HIGH` > `NORMAL` > `LOW` > `BACKGROUND`) when task timers expire simultaneously.
2. **Timing Accuracy**:
   Verifies that tasks are executed at their configured intervals (e.g. 5,000ms for sensors polling, 1,000ms for FSM update).
3. **Overrun Monitoring**:
   Verifies that task durations are tracked. Task execution times exceeding **100ms** trigger scheduler overrun warnings.
4. **Latency Verification**:
   Verifies average loop latency using diagnostics stats.
