# VERSION 4.8.3 — TIME SYNCHRONIZATION & TEMPORAL CONSISTENCY AUDIT

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** V4.8.3 Forensic Time Synchronization & Temporal Consistency Audit  
**Audit Date:** August 18, 2026  
**Status:** Phase 1 Forensic Audit Complete (Zero Source Code Modifications)

---

## Executive Summary

Phase 1 of Milestone V4.8.3 evaluates time handling, timestamp generation, clock synchronization, and temporal consistency across the physical target hardware components (ESP32-WROOM-32 sensor board, ESP32-CAM camera board, and Gateway host).

The audit reveals that while Gateway runtime latency measurements correctly use monotonic timing (`time.perf_counter()`), physical edge device timestamps currently lack SNTP/NTP clock synchronization and explicit synchronization status flags (`time_sync_status`). As a result, unsynchronized edge devices transmit un-synchronized ISO timestamps that cannot be reliably compared for temporal fusion without Gateway-side temporal validation.

---

## Forensic Audit Questionnaire Answers

### 1. Where timestamps are generated
- **Main ESP32 MCU Firmware**: Monotonic time in C++ via `millis()` ([ArduinoTimeProvider.cpp](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/firmware/lib/Scheduler/time/ArduinoTimeProvider.cpp#L5)). Python simulator uses `VirtualRTCSensorDriver` ([sensors.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/iot/drivers/sensors.py#L137)) which generates wall-clock ISO-8601 strings.
- **ESP32-CAM Firmware**: Hardcoded un-synchronized placeholder string `"2026-08-18T10:45:00.000Z"` in [main_esp32_cam.cpp](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/firmware/esp32_cam/main_esp32_cam.cpp#L142).
- **Gateway Receiver**: Attaches `received_at = datetime.now().isoformat()` into `CameraFrame.metadata` upon MQTT message deserialization ([camera_transport.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/cv/camera_transport.py#L210)).

### 2. Monotonic vs. Wall-Clock Time Usage
- **Monotonic Time**: Used in C++ scheduler (`millis()`) and Gateway execution latency tracking (`time.perf_counter()`).
- **Wall-Clock Time**: ISO-8601 strings (`datetime.fromisoformat()`) used for telemetry JSON and camera frame JSON contracts.

### 3. ESP32 NTP Synchronization
- **Current Status**: Neither main ESP32 C++ firmware nor Python `ESP32Device` currently initializes SNTP/NTP network time synchronization on Wi-Fi connection.

### 4. ESP32-CAM NTP Synchronization
- **Current Status**: ESP32-CAM firmware ([main_esp32_cam.cpp](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/firmware/esp32_cam/main_esp32_cam.cpp)) does not initialize SNTP/NTP. It currently transmits a static placeholder ISO timestamp.

### 5. Behavior Before NTP Synchronization Succeeds
- Edge devices transmit un-synchronized or placeholder timestamps. Currently, neither telemetry nor camera message contracts include a `time_sync_status` field (`"SYNCED"` vs `"UNSYNCED"`).

### 6. Gateway Time Authoritativeness
- Gateway host clock is implicitly authoritative for processing timestamps, but incoming camera frames currently lack capture vs. receipt vs. processing timestamp breakdown (`capture_timestamp`, `gateway_receive_timestamp`, `gateway_process_timestamp`).

### 7. Clock Drift Failure Modes
- Unsynchronized edge device clocks drift relative to Gateway wall-clock time. Without explicit `time_sync_status` and sensor-visual delta limits, clock drift can cause valid frames to be misidentified as stale or stale frames to be accepted as fresh.

### 8. Stale & Future Timestamp Safety
- `CameraTransportReceiver` performs a basic sequential check (`curr_dt < last_timestamp`). However, there are no explicit configurable limits for:
  - `MAX_ALLOWED_FRAME_AGE_SEC` (e.g. max 30s)
  - `MAX_FUTURE_TOLERANCE_SEC` (e.g. max 5s)
  - `MAX_SENSOR_VISUAL_DELTA_SEC` (e.g. max 15s)
  - `time_sync_status: "UNSYNCED"` safety fallback.

---

## Architectural Consistency & Design Plan (Phase 2–5)

To address these audit findings in Phase 2–7 implementation:

1. **Hardware Time Contract**: Add `time_sync_status` (`"SYNCED"` vs `"UNSYNCED"`), `capture_timestamp`, `gateway_receive_timestamp`, and `gateway_process_timestamp` to camera and telemetry contracts.
2. **Temporal Validation Module**: Create Gateway-side `TemporalValidator` to enforce configurable limits:
   - Max frame age: `30.0` seconds.
   - Max future tolerance: `5.0` seconds.
   - Max sensor-visual delta: `15.0` seconds.
3. **Safety Fallback**: Un-synchronized, stale, or future timestamps map to `visual_state: CAMERA_FAULT` with explicit reason codes (`VISUAL_TIMESTAMP_INVALID`, `VISUAL_TIMESTAMP_STALE`, `VISUAL_CLOCK_UNSYNCED`).
4. **Safety Assertion**: Invalid timestamps **NEVER** silently produce false `NO_BLOOM` or false `NORMAL`. Sensor evidence remains authoritative.
5. **Frozen V3.8 Source Protection**: Zero modifications to frozen V3.8 files (`esp32_device.py`, `communication.py`, `scheduler.py`, `hal.py`, `actuators.py`).

---

## Forensic Audit Verification Summary

| Component | Timestamp Origin | Time Metric | NTP Sync Active? | Sync Status Flag? |
| :--- | :--- | :--- | :--- | :--- |
| **Main ESP32 Board** | `ArduinoTimeProvider` | Monotonic `millis()` | 🔴 No | 🔴 Missing |
| **ESP32-CAM Board** | `main_esp32_cam.cpp` | Hardcoded String | 🔴 No | 🔴 Missing |
| **Gateway Receiver** | `CameraTransportReceiver` | Wall-Clock ISO | 🟢 Host System | 🔴 Missing |
| **Runtime Orchestrator**| `RuntimeOrchestrator` | Monotonic `perf_counter()` | 🟢 Host System | 🟢 Monotonic Latency |
