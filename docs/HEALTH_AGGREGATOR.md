# Health Aggregator (`HealthAggregator`)

The `HealthAggregator` is responsible for collecting diagnostic snapshots from all active firmware subsystems and building a unified health report.

## Monitored Health Parameters

The aggregator gathers the following parameters:

- **Scheduler Utilization**: CPU scheduling utilization rate (calculated in the cooperative scheduler diagnostics).
- **FSM State**: Current active state of the primary edge FSM.
- **Wi-Fi Connected**: Connection flag reported by the `WiFiManager`.
- **Wi-Fi RSSI**: Wi-Fi signal strength (dBm).
- **MQTT Connected**: Connection status of the MQTT communications broker.
- **Backend Sync State**: FSM state of the device-cloud synchronization gateway.
- **Free Heap**: Real-time free system heap bytes (`ESP.getFreeHeap()`).
- **Battery Level**: Battery voltage percentage.
- **Sensors Healthy**: Health flag compiled from FSM state checks.

## Safety and Isolation

The `HealthAggregator` queries pointers passively, ensuring that health aggregation does not block or execute state modifications on any monitored subsystem.
Obtained statistics are formatted as read-only outputs and passed to observers.
