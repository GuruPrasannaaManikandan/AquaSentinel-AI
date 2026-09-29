# Parallel ESP32 + ESP32-CAM Development Port Configuration Report

**Project:** AquaSentinel-AI — IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Date:** September 29, 2026  
**Scope:** Controlled Development Port Assignment for Simultaneous Dual-Board Hardware Workflows  
**Target Architecture:**
- **Main NodeMCU ESP-32S:** `COM3` (Silicon Labs CP210x USB-to-UART Bridge, `VID:PID = 10C4:EA60`)
- **AI-Thinker ESP32-CAM:** `COM4` (WCH CH340 USB-to-UART on ESP32-CAM-MB, `VID:PID = 1A86:7523`)

---

## 1. Executive Summary

Both microcontrollers are now physically and electrically connected to the host PC simultaneously. A comprehensive audit across the entire repository confirmed that all existing bring-up configurations, PlatformIO targets, and Python companion scripts have been mapped to their respective authoritative ports without touching production firmware, sensor drivers, or GPIO assignments.

---

## 2. Hardware Port Mapping (Physical Verification)

Host USB PnP device enumeration verified:

```text
Port   Device Description                             Hardware ID (VID:PID)   Physical Target
------------------------------------------------------------------------------------------------------------------------
COM3   Silicon Labs CP210x USB to UART Bridge (COM3)  10C4:EA60               Main NodeMCU ESP-32S (Sensors / Actuators)
COM4   USB-SERIAL CH340 (COM4)                        1A86:7523               AI-Thinker ESP32-CAM (GC2145 Camera Node)
```

---

## 3. PlatformIO Environment Audit

All eight independent bring-up environments under `firmware/bringup/` explicitly isolate port ownership:

| Bring-Up Project Directory | Target Hardware | `board` | `upload_port` | `monitor_port` | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `firmware/bringup/01_led_buzzer_relay` | Main ESP32 | `esp32dev` | `COM3` | `COM3` | **PASS** |
| `firmware/bringup/02_led_verification` | Main ESP32 | `esp32dev` | `COM3` | `COM3` | **PASS** |
| `firmware/bringup/03_buzzer_verification` | Main ESP32 | `esp32dev` | `COM3` | `COM3` | **PASS** |
| `firmware/bringup/04_ds18b20_verification` | Main ESP32 | `esp32dev` | `COM3` | `COM3` | **PASS** |
| `firmware/bringup/05_ph_power_verification` | Main ESP32 | `esp32dev` | `COM3` | `COM3` | **PASS** |
| `firmware/bringup/06_esp32_cam_verification`| ESP32-CAM | `esp32cam` | `COM4` | `COM4` | **PASS** |
| `firmware/bringup/07_ov2640_camera_verification`| ESP32-CAM | `esp32cam` | `COM4` | `COM4` | **PASS** |
| `firmware/bringup/08_turbidity_verification`| Main ESP32 | `esp32dev` | `COM3` | `COM3` | **PASS** |

*Note on Production PlatformIO (`firmware/platformio.ini`):* Left completely untouched. For production flashing, `pio run --target upload --upload-port COM3` guarantees explicit targeting without auto-detection ambiguities.

---

## 4. Centralized Python Serial Tooling

To eliminate scattered, hard-coded port strings while preserving backwards compatibility, a centralized configuration module was introduced:

- **New File:** `firmware/bringup/port_config.py`
  - Defines `MAIN_ESP32_PORT = "COM3"` (overridable via `MAIN_ESP32_PORT` env var or CLI argument).
  - Defines `ESP32_CAM_PORT = "COM4"` (overridable via `ESP32_CAM_PORT` env var or CLI argument).

### Updated Bring-Up Scripts
1. `firmware/bringup/08_turbidity_verification/live_monitor.py` -> Linked to `COM3` via `port_config`.
2. `firmware/bringup/08_turbidity_verification/turbidity_verifier.py` -> Linked to `COM3` via `port_config`.
3. `firmware/bringup/06_esp32_cam_verification/monitor_boot.py` -> Linked to `COM4` via `port_config`.
4. `firmware/bringup/07_ov2640_camera_verification/verify_camera.py` -> Linked to `COM4` via `port_config`.
5. `firmware/bringup/07_ov2640_camera_verification/run_all_phases.py` -> Linked to `COM4` via `port_config`.

---

## 5. Live Functional Validation Results

### A. Main ESP32 (`COM3`)
- **COM3 Detection:** **PASS** (Silicon Labs CP210x detected at `VID:PID 10C4:EA60`).
- **PlatformIO Upload:** **PASS** (Flashed `08_turbidity_verification` in 6.27 seconds at 921600 baud, hash verified).
- **Serial Monitor:** **PASS** (115200 baud streaming continuous 100-sample ADC windows).
- **Active Telemetry:** **PASS** (Continuous output from GPIO34 ADC channel).

### B. ESP32-CAM (`COM4`)
- **COM4 Detection:** **PASS** (WCH CH340 detected at `VID:PID 1A86:7523`).
- **Serial Communication:** **PASS** (115200 baud serial stream active).
- **Existing Camera Firmware:** **PASS** (`[HEARTBEAT] Free Heap: 168988 B | Free PSRAM: 4034024 B | Camera: ONLINE 🟢`).

### C. Parallel USB Configuration
- **Simultaneous Connection:** **PASS** (Both boards concurrently active without driver contention).
- **Disambiguation:** **PASS** (Main ESP32 and ESP32-CAM are uniquely addressed by `COM3` and `COM4`).
- **Cross-Flashing Protection:** **PASS** (Explicit port assignments prevent accidental uploads across targets).

---

## 6. System Integrity Confirmation

- **GPIO Assignments Changed:** **NO** (P14, P25, P26, P27, P32, P33, P34 remain unchanged).
- **Production Firmware Changed:** **NO**
- **Production Sensor Drivers Changed:** **NO**
- **Computer Vision Pipeline Changed:** **NO**
- **MQTT Transport Changed:** **NO**
- **AIS Engine Changed:** **NO**
- **FastAPI / Backend Changed:** **NO**
