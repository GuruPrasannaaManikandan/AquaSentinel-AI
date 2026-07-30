# Diagnostics Subsystem Architecture

The diagnostics and fault management framework provides a unified, centralized monitoring layer in the AquaSentinel-AI firmware.

## Architecture Diagram

```
                 [ Cooperative Scheduler Task ]
                                │
                                ▼
                    +───────────────────────+
                    |  DiagnosticsManager   |
                    +───────────┬───────────+
                                │
      ┌─────────────────┬───────┴─────────┬─────────────────┐
      ▼                 ▼                 ▼                 ▼
+───────────+     +───────────+     +───────────+     +───────────+
|  Health   |     | Watchdog  |     |   Fault   |     |   Event   |
|Aggregator |     |  Monitor  |     |  Manager  |     |  Logger   |
+───────────+     +───────────+     +─────┬─────+     +───────────+
                                          │
                                          ▼
                                    +───────────+
                                    |  Fault    |
                                    | Registry  |
                                    +─────┬─────+
                                          │
                                          ▼
                                    +───────────+
                                    | Recovery  |
                                    |  Manager  |
                                    +─────┬─────+
                                          │
                                          ▼
                                   EventDispatcher (FSM triggers)
```

## Core Subsystem Roles

1. **DiagnosticsManager**: Performs coordinates operations, updating sub-modules at the scheduled `DIAGNOSTICS_UPDATE` task rate.
2. **HealthAggregator**: Aggregates CPU load, memory, and connection statuses into a single structured report.
3. **WatchdogMonitor**: Evaluates heartbeat, communication links, and sensor poll durations against safety timing thresholds.
4. **FaultManager**: Directs fault entries, clearance states, severity rankings, and counters.
5. **FaultRegistry**: Bounded database logging up to 20 historical and active faults in static memory.
6. **EventLogger**: A circular log keeping up to 50 general alarms, configurations changes, transitions, and recoveries.
7. **RecoveryManager**: Co-ordinates multi-stage escalations (Retry -> Subsystem Restart -> Safe Shutdown) and triggers FSM state changes via the Event Dispatcher.
