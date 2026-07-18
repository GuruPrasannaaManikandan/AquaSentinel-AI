# Telemetry Contract Report

This report documents the versioned JSON telemetry payload contract transmitted by virtual aquatic monitoring nodes.

## 1. JSON Schema Specification

Every telemetry message published to `aquatic/{device_id}/telemetry` must adhere to this structure:

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "AquaticTelemetryPayload",
    "type": "OBJECT",
    "properties": {
        "schema_version": { "type": "STRING" },
        "device_id": { "type": "STRING" },
        "timestamp": { "type": "STRING", "format": "date-time" },
        "dataset_route": { "type": "STRING", "enum": ["caml", "habsos"] },
        "location": {
            "type": "OBJECT",
            "properties": {
                "latitude": { "type": "NUMBER" },
                "longitude": { "type": "NUMBER" }
            },
            "required": ["latitude", "longitude"]
        },
        "sensors": {
            "type": "OBJECT",
            "properties": {
                "temperature_c": { "type": ["NUMBER", "null"] },
                "salinity_ppt": { "type": ["NUMBER", "null"] },
                "ph": { "type": ["NUMBER", "null"] },
                "turbidity_ntu": { "type": ["NUMBER", "null"] },
                "dissolved_oxygen_mg_l": { "type": ["NUMBER", "null"] }
            },
            "required": ["ph", "turbidity", "dissolved_oxygen_mg_l"]
        },
        "device_health": {
            "type": "OBJECT",
            "properties": {
                "wifi_connected": { "type": "BOOLEAN" },
                "mqtt_connected": { "type": "BOOLEAN" },
                "sensor_status": { "type": "STRING", "enum": ["OK", "FAULT", "DEGRADED"] }
            },
            "required": ["wifi_connected", "mqtt_connected", "sensor_status"]
        }
    },
    "required": ["schema_version", "device_id", "timestamp", "dataset_route", "location", "sensors", "device_health"]
}
```

---

## 2. Parameter Integrity Checks
- **Schema Version:** Set to `"1.0"`.
- **Ecosystem Dataset Route:** Freshwater nodes route to `"caml"`, marine nodes to `"habsos"`.
- **Missing Readings:** If a sensor fails edge-validation or is disconnected, its value is transmitted as `null`. The gateway will handle imputation.
