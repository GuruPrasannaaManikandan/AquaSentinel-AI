# AquaSentinel-AI: Backend Diagnostics (v3.9)

This document describes the parameters tracked by the diagnostics module.

## Metrics Definition

The `BackendDiagnostics` class keeps track of the following variables:

- **Messages Published**: The total count of telemetry, alerts, heartbeats, and diagnostics frames successfully sent to the MQTT broker.
- **Messages Received**: The total count of command packets received on subscribed command topics.
- **Sync Success**: Count of backend commands that were successfully processed and executed.
- **Sync Failure**: Count of command messages that failed parsing, execution, or validation.
- **Reconnect Count**: Count of times the device went from disconnected to connected.
- **Average Sync Time**: The average time (ms) spent handling a command event.
- **Last Sync Timestamp**: The system timestamp (`millis()`) when the last successful command sync took place.

## Payload Layout

These metrics are published periodically (every 30 seconds) in JSON:

```json
{
  "device_id": "AQUA_FRESH_001",
  "publishes": 124,
  "receives": 12,
  "sync_success": 11,
  "sync_failure": 1,
  "reconnects": 1,
  "avg_sync_time_ms": 120,
  "last_sync_timestamp": 240599
}
```
This is monitored on the central dashboard to track edge connectivity stats.
