# Backend Validation

This document outlines the validation checks performed on the Backend Integration Layer.

## Validation Scope

1. **Device Registration**:
   Verifies that the gateway enqueues and publishes device capability payloads (firmware version, hardware revision, features) upon booting.
2. **Telemetry Serialization**:
   Validates that the telemetry JSON payload contains all mandatory keys: `device_id`, `temperature_c`, `ph`, `salinity_ppt`, `turbidity_ntu`, `dissolved_oxygen_mg_l`, `rssi`, `battery_pct`, and `timestamp`.
3. **Dynamic Configuration Updates**:
   Verifies that dynamic configuration updates are received and parsed. Validates interval bounds and rollback behaviors on invalid JSON payloads.
4. **Device Shadow Updates**:
   Confirms that FSM state transitions and connection status changes are mirrored in the local device shadow.
