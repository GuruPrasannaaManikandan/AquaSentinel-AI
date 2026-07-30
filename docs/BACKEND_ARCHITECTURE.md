# AquaSentinel-AI: Backend Integration Layer Architecture (v3.9)

This document provides a high-level overview of the Backend Integration Layer implemented in Version 3.9 of the AquaSentinel-AI firmware.

## Architecture Diagram

The backend integration maintains strict separation of concerns, keeping all device-specific details inside the firmware while communicating over standard JSON-based MQTT channels to the central backend.

```
+------------------------------------------------------------+
|                          FIRMWARE                          |
|                                                            |
|  +--------------+    +--------------+    +--------------+  |
|  |     HAL      |    |     FSM      |    |  Scheduler   |  |
|  +-------+------+    +-------+------+    +-------+------+  |
|          |                   |                   |         |
|          v                   v                   v         |
|  +------------------------------------------------------+  |
|  |                    BackendGateway                    |  |
|  |  (Aggregates telemetry, registrations, & health)     |  |
|  +---------------------------+--------------------------+  |
|                              |                             |
|                              v                             |
|  +------------------------------------------------------+  |
|  |                     MQTTManager                      |  |
|  +------------------------------------------------------+  |
+------------------------------|-----------------------------+
                               |
                        (MQTT Broker)
                               |
                               v
+------------------------------------------------------------+
|                          BACKEND                           |
|                                                            |
|  +------------------------------------------------------+  |
|  |                    Backend Gateway                   |  |
|  |  (FastAPI receiver and validation routing)           |  |
|  +---------------------------+--------------------------+  |
|                              |                             |
|                              v                             |
|  +---------------------------+--------------------------+  |
|  |                     AI Pipeline                      |  |
|  |  (CAML/HABSOS Models, AIS and Evidence Fusion)       |  |
|  +---------------------------+--------------------------+  |
|                              |                             |
|                              v                             |
|  +------------------------------------------------------+  |
|  |               SQLite DB / Web Dashboard              |  |
|  +------------------------------------------------------+  |
+------------------------------------------------------------+
```

## Layer Responsibilities

1. **Firmware Core**: Coordinates raw sensors, tracks state machine changes, and schedules tasks.
2. **Backend Integration Gateway (`BackendGateway`)**: Consumes `MQTTManager` only. It acts as the coordinator, publishing telemetry/alerts, handling device shadow and health state changes, and intercepting backend commands.
3. **MQTT Broker**: Brokering transport channels between the edge device and cloud gateway.
4. **Backend Gateway Service**: Validates schemas and routes payload to AI and database storage.

## Communication Patterns
- **Publish Telemetry**: Publishes formatted JSON sensor readings periodically to `aquatic/<device_id>/telemetry`.
- **Receive Commands**: Listens to `aquatic/<device_id>/command` for instructions from the server.
- **Heartbeat & Shadow**: Publishes status and synchronization frames to `aquatic/<device_id>/status`.
- **Diagnostics**: Tracks round-trip times and failures, logging them to `aquatic/<device_id>/diagnostics`.
