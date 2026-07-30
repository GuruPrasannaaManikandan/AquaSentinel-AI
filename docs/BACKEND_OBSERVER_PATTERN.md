# Backend Observer Pattern

To maintain separation of concerns and allow multiple modules to monitor synchronization events, the `BackendGateway` implements a read-only Observer Pattern.

## Class Diagram

```
  +───────────────────────+
  |   IBackendObserver    | <── Interface
  +───────────────────────+
  | + onSyncStateTransition()
  | + onConfigUpdated()
  | + onTelemetryBuffered()
  | + onTelemetryDropped()
  | + onDiagnosticsSynced()
  +───────────────────────+
              ▲
              │ (Inherits)
      ┌───────┴───────┬──────────────┐
      │               │              │
+─────┴─────+  +──────┴──────+  +────┴────+
|  Logger   |  | Diagnostics |  | etc.    |
+───────────+  +─────────────+  +─────────+
```

## Observers List

1. **Logger**: Writes FSM transitions, config updates, and offline buffers warnings to the Serial interface.
2. **Diagnostics**: Feeds synchronizations success and latency rates into the `BackendDiagnostics` database.
3. **Dashboard**: Connects the telemetry outputs to local indicators.
4. **Cloud Monitor**: Syncs connection sessions to session logs.

## Read-Only Constraints

To protect the core synchronization FSM, **observers are strictly read-only**:
- All callback parameters are passed as `const` references or values (e.g. `const TelemetryData&`).
- Observers do not hold a pointer to the `BackendGateway` and cannot call setter methods, preventing circular transitions or state modifications during notification dispatches.
- If an observer needs to trigger actions, it must do so by publishing an event to the `EventDispatcher` queue.
