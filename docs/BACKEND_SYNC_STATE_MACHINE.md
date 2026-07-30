# Backend Synchronization State Machine

The Backend Integration Layer operates a deterministic synchronization state machine.

```
                    +─────────────────+
                    |  UNREGISTERED   |
                    +────────┬────────+
                             │  (WiFi & MQTT Connected)
                             ▼
                    +─────────────────+
                    |   REGISTERING   |
                    +────────┬────────+
                             │  (Registration Success)
                             ▼
                    +─────────────────+
                    |   REGISTERED    |
                    +────────┬────────+
                             │  (Active Status)
                             ▼
                    +─────────────────+
       ┌───────────►|  SYNCHRONIZED   |<───────────┐
       │            +────────┬────────+            │
       │                     │ (Send Telemetry)    │
       │                     ▼                     │
(Telemetry Sent)    +─────────────────+      (Reconnect & Flush)
       │            |     SYNCING     |            │
       └────────────+────────┬────────+            │
                             │ (Disconnect)        │
                             ▼                     │
                    +─────────────────+            │
                    |   RECOVERING    |────────────┘
                    +─────────────────+
```

## State Definitions

1. **`UNREGISTERED`**: Base offline state upon boot.
2. **`REGISTERING`**: Establishing connection, publishing device capabilities.
3. **`REGISTERED`**: Registration accepted, subscribing to config topics.
4. **`SYNCING`**: Active upload session (telemetry/alerts).
5. **`SYNCHRONIZED`**: In idle state, listening for commands and config updates.
6. **`RECOVERING`**: Connection dropped. Caching telemetry to offline queue.
7. **`FAILED`**: Maximum retry limits exceeded. Reconnect backoff active.

## Transition Rules, Guards & Actions

| From State | To State | Transition Guard (Condition) | Transition Action (Execution) |
| --- | --- | --- | --- |
| **`UNREGISTERED`**| **`REGISTERING`**| WiFi & MQTT connected | `actionRegisterDevice()` |
| **`REGISTERING`** | **`REGISTERED`** | Registration reply received | `actionRequestConfiguration()` |
| **`REGISTERED`**  | **`SYNCHRONIZED`**| Config subscription OK | Enters normal loop |
| **`SYNCHRONIZED`**| **`SYNCING`** | Telemetry schedule triggers | Publishes telemetry packet |
| **`SYNCING`**     | **`SYNCHRONIZED`**| Telemetry publish success | Updates shadow cache |
| **`ANY`**         | **`RECOVERING`** | WiFi or MQTT disconnected | Logs session history |
| **`RECOVERING`**  | **`REGISTERING`**| WiFi & MQTT connected | `actionFlushOfflineQueue()` |
| **`REGISTERING`** | **`FAILED`**     | Registration fails/retries fail| Backs off, retries later |
