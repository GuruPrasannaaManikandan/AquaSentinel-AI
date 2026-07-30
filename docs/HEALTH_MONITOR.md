# AquaSentinel-AI: Health Monitor (v3.9)

This document describes how the edge node monitors its internal system health and resources.

## System Health Metrics

The `HealthMonitor` class queries various system layers to report local hardware status:

- **CPU Load**: Exposed as the CPU utilization ratio of the cooperative task scheduler (%).
- **Heap Usage**: Calculated on target dynamically via ESP32 SDK functions (`ESP.getFreeHeap()` and `ESP.getHeapSize()`).
- **Task Execution Time**: The longest execution latency recorded among all scheduler tasks (us).
- **Wi-Fi Status**: Cast integer value of the current `WiFiState` enum.
- **MQTT Status**: Cast integer value of the current `MQTTState` enum.
- **Sensor Status**: Health of the calibrated sensor array (`OK`, `WARNING`, `FAULT`).
- **Uptime**: System runtime seconds.

## Health Output Format

These metrics are compiled into a `HealthMetrics` block:

```json
{
  "cpu_load_pct": 12.5,
  "free_heap_bytes": 245388,
  "total_heap_bytes": 327680,
  "longest_task_execution_us": 1240,
  "wifi_status": 3,
  "mqtt_status": 2,
  "sensor_status": "OK",
  "uptime_seconds": 1245
}
```
This is merged into the diagnostics and shadow payloads synchronized with the backend.
