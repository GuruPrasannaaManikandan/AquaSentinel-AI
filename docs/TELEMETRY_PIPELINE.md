# AquaSentinel-AI: Telemetry Pipeline (v3.9)

This document describes the data formatting and transport pipeline of sensor telemetry.

## Telemetry Payload Schema

Telemetry is sent to the topic:
`aquatic/<device_id>/telemetry`

### JSON Schema

The payload follows a schema validated by the backend gateway:

```json
{
  "schema_version": "1.0",
  "device_id": "AQUA_FRESH_001",
  "timestamp": "2026-07-29T13:51:08Z",
  "sequence_number": 42,
  "dataset_route": "caml",
  "location": {
    "latitude": 27.5,
    "longitude": -81.2
  },
  "sensors": {
    "temperature_c": 25.4,
    "salinity_ppt": 0.5,
    "ph": 7.2,
    "turbidity_ntu": 4.5,
    "dissolved_oxygen_mg_l": 6.8,
    "battery": 98.5,
    "rssi": -60,
    "distance_to_water_m": 120.0,
    "sample_depth": 0.0
  },
  "device_health": {
    "wifi_connected": true,
    "mqtt_connected": true,
    "sensor_status": "OK"
  }
}
```

## Payload Field Definition

- **`schema_version`**: String version of this JSON schema ("1.0").
- **`device_id`**: Matches the unique device registry identifier (e.g. `AQUA_FRESH_001`).
- **`timestamp`**: ISO 8601 formatted UTC date-time string.
- **`sequence_number`**: An incrementing counter tracking sent telemetry frames.
- **`dataset_route`**: Routes to either `"caml"` (Freshwater) or `"habsos"` (Marine) AI models.
- **`location`**: Sub-object containing latitude/longitude coordinates.
- **`sensors`**:
  - `temperature_c`: Water temperature.
  - `salinity_ppt`: Water salinity.
  - `ph`: Water pH.
  - `turbidity_ntu`: Water turbidity.
  - `dissolved_oxygen_mg_l`: Water Dissolved Oxygen level.
  - `battery`: Device battery level (%).
  - `rssi`: Wi-Fi signal strength in dBm.
- **`device_health`**: Contains status checks for network and sensor faults.

## Diagnostics and Failures

If the telemetry structure is invalid or lacks mandatory keys, the backend logs a validation failure to the database under the status `FAULT` and bypasses AI inference.
If the `sensor_status` is flagged as `FAULT`, the gateway automatically defaults to the `SENSOR_FAULT_BYPASS` state, ignoring ML model calculations and publishing the `CRITICAL` decision state.
