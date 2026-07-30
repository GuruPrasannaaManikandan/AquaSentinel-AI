# Expanded Backend Diagnostics (v2)

This document describes the parameters tracked by the expanded diagnostics module.

## Extended Diagnostics Metrics

In addition to basic counts, the revised diagnostics layer tracks production metrics:

- **`publishes`**: Successful MQTT publish frames.
- **`receives`**: Incoming MQTT command frames.
- **`sync_success`**: Correctly executed command updates.
- **`sync_failure`**: Rejected or malformed commands.
- **`reconnects`**: Connection drop recovery count.
- **`avg_sync_time_ms`**: Average round-trip synchronization latency (ms).
- **`success_rate_pct`**: Success rate percentage of synchronization processes.
- **`failure_rate_pct`**: Failure rate percentage.
- **`config_updates`**: Successfully applied versioned configuration changes.
- **`rollbacks`**: Count of rolled-back configuration updates.
- **`offline_buffer_usage`**: Current item count in the offline queue.
- **`dropped_telemetry`**: Telemetry frames dropped due to buffer overflow.
- **`session_duration_sec`**: Total uptime (seconds) accumulated while connected.

## Serialization Format

Diagnostics are published to `aquatic/<device_id>/diagnostics`:

```json
{
  "device_id": "AQUA_FRESH_001",
  "publishes": 1450,
  "receives": 45,
  "sync_success": 42,
  "sync_failure": 3,
  "reconnects": 2,
  "avg_sync_time_ms": 142,
  "success_rate_pct": 93.3,
  "failure_rate_pct": 6.7,
  "config_updates": 3,
  "rollbacks": 1,
  "offline_buffer_usage": 0,
  "dropped_telemetry": 0,
  "session_duration_sec": 7245
}
```
