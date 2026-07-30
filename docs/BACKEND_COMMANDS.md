# AquaSentinel-AI: Backend Commands (v3.9)

This document describes the command architecture enabling backend operators to control the device remotely.

## Command Routing Path

```
Server REST API
     |
     v
MQTT Command Topic (aquatic/{device}/command)
     |
     v
BackendGateway::onMessageReceived()
     |
     v (Translates to Event cast & publishes)
EventDispatcher Queue
     v (Asynchronous Dequeue in BACKEND_UPDATE Task)
BackendCommandHandler::handleCommand()
     |
     +---- SENSORS_READY ----> FSM (Starts Polling)
     +---- SHUTDOWN_REQUEST -> FSM (Stops/Enters Shutdown)
     +---- PING -------------> Publishes PONG response
     +---- RESET ------------> ESP.restart()
```

## Supported Commands

| Command | Event Cast ID | Action | Result |
| --- | --- | --- | --- |
| **`START`** | `100` | Publishes `Event::SENSORS_READY` | FSM transitions `IDLE` -> `MONITORING` |
| **`STOP`** | `101` | Publishes `Event::SHUTDOWN_REQUEST` | FSM transitions to `SHUTDOWN` |
| **`CALIBRATE`** | `102` | Runs calibration diagnostics | Evaluates sensors and returns validation |
| **`RESET`** | `103` | Reboots the microcontroller | Microcontroller software restart (`ESP.restart()`) |
| **`PING`** | `104` | Replies with a PONG status packet | Publishes `{"status":"pong"}` to `aquatic/+/status` |
| **`HEARTBEAT`**| `105` | Intercepts remote heartbeat requests | Diagnostic trace logged |
| **`OTA_READY`**| `106` | Prepares for future OTA firmware downloads| Future OTA integration placeholder |

## JSON Command Message Schema

Received on the topic `aquatic/<device_id>/command`:

```json
{
  "command": "START",
  "device_id": "AQUA_FRESH_001",
  "payload": {}
}
```
