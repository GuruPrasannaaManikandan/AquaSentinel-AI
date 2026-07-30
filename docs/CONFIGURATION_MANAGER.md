# Configuration Manager (`ConfigurationManager`)

The `ConfigurationManager` handles dynamically receiving, validating, versioning, applying, and rolling back configuration settings received from the backend over MQTT.

## Architectural Design

To prevent unstable firmware configurations, **configuration settings are never applied directly**. Instead:
1. A new configuration payload is received on the topic `aquatic/<device_id>/configuration`.
2. The payload is parsed into an in-memory `BackendConfig` buffer.
3. The configuration fields (telemetry, heartbeat, and diagnostics intervals) are validated against hardcoded safety boundary limits.
4. If validation succeeds, the current settings are saved to `_previousConfig`, the new configuration is marked active, and changes are applied to the `BackendSyncPolicy`.
5. If validation fails, a **rollback action** is executed immediately, discarding the changes and restoring the previous settings. This failure is recorded in the diagnostics database.

```
       Incoming JSON Payload
                 │
                 ▼
     [ JSON Deserialization ]
                 │
                 ▼
     [ Validation Boundaries ] ──(Invalid)──► [ Rollback Configuration ]
                 │                                      │
              (Valid)                                   ▼
                 │                          Increment Rollback Count
                 ▼                          Maintain Safety Defaults
       [ Save to Previous ]
                 │
                 v
       [ Apply Active Config ]
                 │
                 ▼
    [ Update BackendSyncPolicy ]
```

## Safety Bounds

Validation constraints enforced at compile-time:
- **Telemetry Interval**: Between 1,000 ms and 60,000 ms.
- **Heartbeat Interval**: Between 1,000 ms and 60,000 ms.
- **Diagnostics Interval**: Between 5,000 ms and 120,000 ms.
- **Version String**: Must be non-empty.

## Config Message Schema

Example valid JSON payload:

```json
{
  "version": "1.2",
  "telemetry_interval": 5000,
  "heartbeat_interval": 10000,
  "diagnostics_interval": 30000
}
```
