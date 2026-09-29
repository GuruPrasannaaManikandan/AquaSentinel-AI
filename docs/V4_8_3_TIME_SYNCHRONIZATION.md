# VERSION 4.8.3 — TIME SYNCHRONIZATION & TEMPORAL CONSISTENCY

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** V4.8.3 Time Synchronization & Temporal Consistency Implementation  
**Completion Date:** August 18, 2026  
**Verified Test Baseline:** 275 passed, 3 skipped (278 total pytest items), 244/244 core Phase 9 assertions  
**V3.8 Source Code Modifications:** ZERO (0) (Verified via `git status`)

---

## Architecture Diagram

```
             ┌──────────────────┐
             │   ESP32-WROOM    │
             │ Sensors + NTP    │
             └────────┬─────────┘
                      │
                 Telemetry
                      │
                      ▼
                 ┌─────────┐
                 │ Gateway │
                 └────┬────┘
                      ▲
                      │ MQTT (Schema 1.1)
                      │
             ┌────────┴─────────┐
             │    ESP32-CAM     │
             │ Camera + NTP     │
             └──────────────────┘
                      │
              capture_timestamp
                      │
                      ▼
              TemporalValidator
                      │
          ┌───────────┴───────────┐
          │                       │
       VALID                    INVALID
          │                       │
          ▼                       ▼
      CV Pipeline            Sensor-only
          │                    fallback
          ▼
      V4.5 Fusion
          │
          ▼
      V4.6 Decision
          │
          ▼
      V4.7 Runtime
```

---

## Executive Summary

Version 4.8.3 establishes a hardware-ready **Time Synchronization & Temporal Consistency Layer** for physical hardware deployment across:
1. **ESP32-WROOM-32 Sensor/Actuator Board** (C++ `TimeSyncManager.h` using SNTP / `configTime`).
2. **ESP32-CAM AI-Thinker OV2640 Board** (C++ SNTP wall-clock capture timestamp & `time_sync_status` flag).
3. **Gateway Host** (`TemporalValidator` in [temporal_validator.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/cv/temporal_validator.py)).

---

## 1. Multi-Tier Timestamp Architecture

Every acquired camera frame preserves three distinct non-overwriting timestamps:

- **`capture_timestamp`**: Generated on the camera board representing the exact moment of frame acquisition.
- **`gateway_receive_timestamp`**: Generated on the Gateway host when the MQTT frame payload is ingested.
- **`gateway_process_timestamp`**: Generated on the Gateway host when pipeline evaluation begins.

---

## 2. Gateway Temporal Validation Thresholds

Configured in `TemporalValidator` ([temporal_validator.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/cv/temporal_validator.py)):

- **`MAX_ALLOWED_FRAME_AGE_SEC = 30.0 s`**: 3x sensor sampling interval of 10s; prevents stale or buffered frames from entering multimodal fusion.
- **`MAX_FUTURE_TOLERANCE_SEC = 5.0 s`**: Window allowing for minor clock skew without false rejection.
- **`MAX_SENSOR_VISUAL_DELTA_SEC = 15.0 s`**: 1.5x sensor sampling interval; ensures visual evidence is temporally aligned with sensor telemetry.

---

## 3. Un-Synchronized Edge Device Safety & Fallback

When an edge device has not completed SNTP synchronization (`time_sync_status == "UNSYNCED"`):
- The device **NEVER** fabricates a fake absolute timestamp.
- The Gateway marks `temporal_valid = False` and `reason_code = VISUAL_CLOCK_UNSYNCED`.
- Visual evidence is set to `visual_state: CAMERA_FAULT`.
- `FusionEngine` falls back to base sensor evidence (ML + AIS) under reason code `VISUAL_CLOCK_UNSYNCED`.

> [!IMPORTANT]
> **SAFETY ASSERTION**: Temporal invalidity **NEVER** silently produces false `NO_BLOOM` or false `NORMAL`.

---

## 4. Reason Code Mapping Matrix

| Temporal Condition | Status Code | Temporal Valid? | Reason Code | Fusion Fallback State |
| :--- | :--- | :--- | :--- | :--- |
| **Valid Synced Frame** | `VALID` | 🟢 True | `OK` | Multimodal Fused State |
| **Un-synchronized Node**| `UNSYNCED` | 🔴 False | `VISUAL_CLOCK_UNSYNCED` | Sensor Decision Preserved |
| **Stale Frame (>30s)** | `STALE` | 🔴 False | `VISUAL_TIMESTAMP_STALE` | Sensor Decision Preserved |
| **Future Frame (>5s)** | `FUTURE_TIMESTAMP` | 🔴 False | `VISUAL_TIMESTAMP_FUTURE` | Sensor Decision Preserved |
| **Clock Skew (>15s)** | `CLOCK_SKEW` | 🔴 False | `VISUAL_CLOCK_SKEW` | Sensor Decision Preserved |
| **Invalid ISO Syntax** | `INVALID_TIMESTAMP`| 🔴 False | `VISUAL_TIMESTAMP_INVALID`| Sensor Decision Preserved |

---

## 5. Frozen V3.8 Protection Confirmation

Empirical verification via `git status --porcelain`:
- `src/iot/esp32_device.py`: **UNTOUCHED (0 modifications)**
- `src/iot/communication.py`: **UNTOUCHED (0 modifications)**
- `src/iot/scheduler.py`: **UNTOUCHED (0 modifications)**
- `src/iot/hal.py`: **UNTOUCHED (0 modifications)**
- `src/iot/actuators.py`: **UNTOUCHED (0 modifications)**
