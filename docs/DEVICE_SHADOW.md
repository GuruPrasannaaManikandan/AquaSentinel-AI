# AquaSentinel-AI: Device Shadow (v3.9)

This document describes the Device Shadow state system.

## Purpose

The Device Shadow provides a local in-memory representation of the device's state. It caches the latest status values so they can be queried or synchronized with the backend.

```
+-----------------------------------------------------------+
|                       DeviceShadow                        |
|                                                           |
|  +-------------------------+  +------------------------+  |
|  |     Metadata Cache      |  |  Latest Readings Cache  |  |
|  |                         |  |                        |  |
|  |  - FSM State            |  |  - Temperature         |  |
|  |  - Sensor Status        |  |  - pH                  |  |
|  |  - Network Status       |  |  - Dissolved Oxygen    |  |
|  |  - Firmware Version     |  |  - Turbidity           |  |
|  |  - Configuration Ver    |  |  - Salinity            |  |
|  +-------------------------+  +------------------------+  |
|                                                           |
|                       +------------------+                |
|                       |    Last Alert    |                |
|                       +------------------+                |
+-----------------------------------------------------------+
```

## Structure Definition

The in-memory shadow matches the `ShadowState` structure:

- **`currentState`**: The current FSM state (int enum).
- **`sensorStatus`**: Character string representing sensor faults (`OK`, `WARNING`, `FAULT`).
- **`networkStatus`**: Network state (`CONNECTED`, `DISCONNECTED`).
- **`firmwareVersion`**: Loaded firmware version.
- **`configurationVersion`**: Loaded config schema version.
- **`lastTemperature`, `lastPH`, `lastDO`, `lastTurbidity`, `lastSalinity`**: Sensor value cache.
- **`lastAlert`**: Description of the last alert triggered.

## Synchronization

The shadow is updated:
1. Every time a new telemetry reading is taken (`updateTelemetry()`).
2. When FSM transitions occur (`updateFSMState()`).
3. On Wi-Fi connection drops or reconnects (`updateNetworkStatus()`).
4. When alerts are generated (`updateLastAlert()`).
