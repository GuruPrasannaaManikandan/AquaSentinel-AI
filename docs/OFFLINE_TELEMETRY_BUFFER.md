# Offline Telemetry Buffer (`OfflineTelemetryBuffer`)

The `OfflineTelemetryBuffer` acts as a static FIFO buffer that caches telemetry readings when the device is disconnected from the backend.

## Architectural Objectives

1. **Memory Stability**: Uses a static, fixed-size array (`OFFLINE_BUFFER_CAPACITY = 20`) of `TelemetryData` blocks. It performs **no dynamic memory allocations** (e.g. `malloc` or `new`), which avoids heap fragmentation and out-of-memory crashes.
2. **Overflow Resiliency**: If the queue fills up, new pushes trigger an overflow flag. The oldest entry is overwritten (`circular overwrite`), and the diagnostics layer increments the `droppedTelemetry` count.
3. **Automated Flush**: Upon connection recovery, the gateway transitions through `REGISTERING` and flushes all queued telemetry items to the broker in FIFO order.

## Processing Flow

```
                      +-------------------+
                      |   TelemetryData   |
                      +---------┬---------+
                                │
                                v
               [ Wi-Fi / MQTT Connected? ]
                      /           \
                 (No)               (Yes)
                  /                   \
                 v                     v
     +───────────────────────+   +───────────+
     | OfflineTelemetryBuffer|   | Send to   |
     |                       |   | MQTT      |
     | - push() to array     |   +───────────+
     | - FIFO Circular FIFO  |
     | - Overwrite if full   |
     +───────────────────────+
                 │
            (Reconnect)
                 │
                 ▼
     +───────────────────────+
     | Flush Cache (pop)     |
     | Send elements in FIFO |
     +───────────────────────+
```
