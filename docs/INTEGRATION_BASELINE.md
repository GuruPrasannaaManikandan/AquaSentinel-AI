# AquaSentinel-AI — Integration Baseline Snapshot (Phase 0)

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems (AquaSentinel-AI)  
**Milestone:** Hardware–Software Integration Master Implementation  
**Phase:** Phase 0 — Baseline Snapshot  
**Execution Timestamp:** 2026-09-29T01:52:00+05:30  
**Branch:** `feature/hardware-integration` (branched from `main`)  
**Base Commit:** `03efa2b21236db8ba6253bb7d2e3fc1a8cfa07d7` (`Comitted`)  
**Status:** PASS — BASELINE VERIFIED & FROZEN  

---

## 1. Git Repository State

- **Active Branch:** `feature/hardware-integration`
- **Parent Branch:** `origin/main`
- **Head Commit Hash:** `03efa2b21236db8ba6253bb7d2e3fc1a8cfa07d7`
- **Commit Author:** GuruPrasannaaManikandan <prasannaavijayakumar2006@gmail.com>
- **Commit Date:** Tue Aug 18 10:44:30 2026 +0530
- **Working Tree Pre-Existing Changes:**
  - 49 modified files and untracked documentation/test suites resulting from prior Capstone milestones (V4.8 through V8.0).
  - All pre-existing modifications are verified as known prior milestone artifacts and will be preserved untouched.

---

## 2. Firmware Build Baseline (Main ESP32)

- **Target Environment:** `esp32dev` (`firmware/platformio.ini`)
- **Microcontroller:** Espressif ESP32-D0WD-V3 (240MHz Xtensa Dual-Core, 320KB RAM, 4MB Flash)
- **Framework:** Arduino / ESP-IDF (Platform: `espressif32 @ 7.0.1`, Toolchain: `xtensa-esp32 @ 8.4.0`)
- **Compilation Command:** `pio run -d firmware`
- **Compilation Exit Code:** `0` (SUCCESS)
- **Compilation Duration:** 4.90 seconds
- **Memory Consumption:**
  - **RAM Utilization:** 29,028 bytes / 327,680 bytes (**8.9%**)
  - **Flash Utilization:** 342,637 bytes / 1,310,720 bytes (**26.1%**)
- **Dependency Resolution:**
  - `ArduinoJson @ 6.21.6`
  - `PubSubClient @ 2.8.0`
  - `OneWire @ 2.3.8`
  - `DallasTemperature @ 3.11.0`
  - Internal static libraries: `PhysicalDrivers`, `MockDrivers`, `Backend`, `Calibration`, `Diagnostics`, `FSM`, `MQTT`, `WiFi`, `Scheduler`, `Verification`

---

## 3. Firmware Build Baseline (ESP32-CAM)

- **Production Source Target:** `firmware/esp32_cam/main_esp32_cam.cpp` (8,467 bytes)
- **Bring-Up Verified Source:** `firmware/bringup/07_ov2640_camera_verification/07_ov2640_camera_verification.ino` (27,148 bytes)
- **Hardware Architecture:** AI-Thinker ESP32-CAM with 4MB External PSRAM, GalaxyCore GC2145 sensor (PID `0x2145`).
- **Baseline Diagnostic:** The standalone file `main_esp32_cam.cpp` currently contains the legacy `PIXFORMAT_JPEG` contract (targeted for overhaul in Phase 6). Verified standalone compile occurs in the bring-up environment.

---

## 4. Hardware Port Baseline

- **Main ESP32:** Silicon Labs CP2102 USB-to-UART Bridge on **`COM3`**
- **ESP32-CAM:** WCH CH340 USB-to-UART Bridge on **`COM4`**
- **Simultaneous Operation:** Verified stable without port swapping.

---

## 5. Verification Gate Status

- [x] Branch `feature/hardware-integration` created and active.
- [x] Clean baseline compile of Main ESP32 firmware established.
- [x] Pre-existing changes inventoried and protected from overwriting.
- [x] Authoritative baseline documentation frozen.

**Gate 0 Conclusion:** Phase 0 is complete and successful. Authorization granted to proceed to **Phase 1 — Authoritative Configuration**.
