# Fault Manager (`FaultManager`)

The `FaultManager` provides operational interfaces to log, list, clear, and count errors occurring across the firmware execution space.

## Severity Classification

Faults are classified into four severity levels:

1. **`INFO`**: Diagnostic messages, configuration adjustments, or general updates. Requires no recovery action.
2. **`WARNING`**: Non-critical threshold deviations or temporary latency overruns. Triggers retries or warning transitions.
3. **`ERROR`**: Device or communication failures (e.g. sensor timeout or link disconnected). Triggers subsystem restarts and recovery loops.
4. **`CRITICAL`**: Complete hardware failure or repeated unrecovered errors. Escalates to safe shutdowns.

## Fault Registry Bindings

The `FaultManager` binds to the static `FaultRegistry`:
- Registers new faults, which automatically logs their initial detection.
- Tracks occurrences of up to 50 unique fault IDs in static counters.
- Triggers active fault queries to determine the highest active severity.
- Marks resolved faults as inactive and flags them as `RESOLVED`.
