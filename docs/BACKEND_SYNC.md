# AquaSentinel-AI: Backend Synchronization (v3.9)

This document describes how state is kept in sync between the device firmware and backend gateway.

## Synchronization Channels

State synchronization is handled through three primary mechanisms:

1. **Heartbeat Messages**:
   - Sent every 10 seconds to `aquatic/<device_id>/status`.
   - Re-asserts the online status of the device, reporting uptime, current sensor health, and firmware version.
   
2. **Device State Sync**:
   - Compiles FSM transition changes and network connection shifts, updating the `DeviceShadow` cache.
   - Synchronizes shadow properties with the backend on change.
   
3. **Diagnostics Reporting**:
   - Sent every 30 seconds to `aquatic/<device_id>/diagnostics`.
   - Sends the aggregated diagnostics data collected by `BackendDiagnostics`.

## Reconnect Recovery Sequence

When the device drops connection and reconnects:
1. Re-subscribes to command and decision topics:
   `aquatic/<device_id>/command`
   `aquatic/<device_id>/decision`
2. Immediately publishes a Device Registration message to register capabilities.
3. Publishes an updated Heartbeat frame to assert it is online.
4. Resets the sync failure metrics.
