# AquaSentinel-AI: Device Registration (v3.9)

This document describes how an edge device registers itself dynamically to the backend registry on startup or reconnect recovery.

## Registration Process

When the device starts up or recovers from a connection drop, the `BackendGateway` sends a registration frame.

```
Device (Edge)                          MQTT Broker                          Backend Gateway
     |                                      |                                      |
     |---- Publish registration ----------->|                                      |
     |     Topic: aquatic/+/status          |                                      |
     |                                      |---- Route to service --------------->|
     |                                      |                                      | (Verifies registry)
```

### Registration JSON Payload

Published to `aquatic/<device_id>/status`:

```json
{
  "device_id": "AQUA_FRESH_001",
  "firmware_version": "3.9.0",
  "hardware_revision": "ESP32-WROOM-32E",
  "capabilities": [
    "gps",
    "rtc",
    "temperature",
    "salinity",
    "ph",
    "turbidity",
    "dissolved_oxygen"
  ],
  "location": {
    "latitude": 27.5,
    "longitude": -81.2
  },
  "registration_status": "REGISTERED"
}
```

## Payload Field Definition

- **`device_id`**: Matches the unique device registry identifier.
- **`firmware_version`**: The running firmware release version (e.g. `3.9.0`).
- **`hardware_revision`**: Microcontroller model/revision type.
- **`capabilities`**: List of enabled sensors and peripherals.
- **`location`**: Coordinates where the node is anchored.
- **`registration_status`**: Represents the current registration lifecycle status (`UNREGISTERED`, `REGISTERING`, `REGISTERED`, `FAILED`).
