# System Verification Plan

This document outlines the end-to-end verification plan for the AquaSentinel-AI firmware, specifying how each module is validated using non-intrusive self-tests.

## Verification Hierarchy

```
       [ setup() Startup Trigger ]
                    │
                    ▼
        +─────────────────────────+
        |   VerificationManager   |
        +───────────┬─────────────+
                    │
       ┌────────────┴─────────────┐
       ▼                          ▼
+──────────────+           +──────────────+
| Hardware     |           | System       |
| Self-Tests   |           | Test Runner  |
+──────┬───────+           +──────┬───────+
       │                          │
       ├─ HAL Drivers Check       ├─ Normal Operation Scenarios
       ├─ ADC Sensor Bounds       ├─ Wi-Fi Disconnection Buffering
       ├─ GPIO Output Writes      ├─ MQTT Broker Disconnection
       ├─ Memory Allocations      ├─ Recovery & Flush Buffers
       └─ OS/FSM States Check     └─ Timeout Watchdog Triggers
```

## Non-Intrusive Validation Workflow

To test network loss, sensor errors, and task delays without physical hardware, the verification suite integrates directly with the mock services:
- **`MockWiFiService`**: Disconnected programmatically to verify buffering.
- **`MockMQTTService`**: Disconnected to verify reconnect recovery loops.
- **`HAL` / `MockDrivers`**: Fed out-of-bound ADC values to check sensor validation rules.
- **`Scheduler` / `FSM`**: Checked for task registrations and valid state transitions.
- **`DiagnosticsManager`**: Tracked for watchdog alarms and recovery triggers.
- **`BackendGateway`**: Checked for registrations, shadows, configurations, and flushing.
