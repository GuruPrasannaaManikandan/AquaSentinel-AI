# Watchdog Monitor (`WatchdogMonitor`)

The `WatchdogMonitor` provides software-defined watchdog supervision to prevent device lockups, task overruns, and communication silence.

## Watchdog Supervisions

1. **Heartbeat Watchdog**:
   Tracks the duration since the last heartbeat tick. If it exceeds **30 seconds**, it registers a `WARNING` fault.
2. **Communication Watchdog**:
   Tracks duration since the last successful MQTT exchange. If it exceeds **60 seconds**, it registers an `ERROR` fault.
3. **Sensor Watchdog**:
   Monitors sensor polling tasks. If reads freeze and the time since the last success exceeds **15 seconds**, it registers a sensor timeout `ERROR` fault.
4. **Task Overrun Watchdog**:
   Checks scheduler execution. If a task's longest execution time exceeds **100 milliseconds** (`100000 us`), it registers a `WARNING` fault.
5. **CPU Load Watchdog**:
   Monitors processor load. If scheduler utilization exceeds **95%**, it registers a warning fault to prevent lockups.

## Feed Mechanism

Watchdog timers are fed during scheduler task loops:
- Heartbeats feed the watchdog during `heartbeatTask`.
- MQTT transactions feed the watchdog during `mqttUpdateTask`.
- Sensor polling feeds the watchdog during `sensorPollingTask`.
If a task freezes, the watchdog tick will time out and trigger recovery escalation.
