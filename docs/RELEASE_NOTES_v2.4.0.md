# Release Notes - Version 2.4.0 (Release Candidate 1)

This release officially freezes the Version 2 embedded-ready system architecture.

---

## 1. Overview of Key Features

*   **Cooperative Task Scheduler:** Implemented FreeRTOS-like task coordinator supporting sorted priorities, message queues, and thread-safe event flags.
*   **Hardware Abstraction Layer (HAL):** Decoupled pin structures and calibration logic from core device loops.
*   **Modular Virtual Drivers:** Separated sensors and actuators into abstract base definitions (`BaseSensorDriver` / `BaseActuatorDriver`).
*   **Independent Device Runner:** Created a standalone process runner at `embedded_device/main.py` mimicking a remote ESP32.
*   **Centralized Configuration:** Moved all GPIO pins, operational thresholds, scaling multipliers, offsets, and topics to `config/device_config.json`.

---

## 2. Bug Fixes

*   **Streamlit DeltaGenerator Bug:** Restructured the alert log ternary condition statement to standard block statements to prevent Streamlit's parser from rendering the return `DeltaGenerator` objects on screen.
*   **Centralized Calibration Limits:** Removed hardcoded ranges from the `EdgeValidator` and linked them to the config file boundaries dynamically.

---

## 3. Performance & Throughput Benchmarks

*   **Processing Overhead:** Stepping cooperative tasks takes less than `0.1 ms` on Python 3.13.9.
*   **Sustained Stress Capacity:** Processing telemetry-to-fusion pipeline executes at **19.57 cycles/sec** with average latency of **51.09 ms**.

---

## 4. Testing & Verification Summary

*   **Automated Pytest Suite:** 186 unit and integration checks passing.
*   **Decoupled Integration Tests:** Passed end-to-end telemetry, network disconnect-reconnect loops, fault bypass routes, and runtime driver swaps in `tests/integration_test_v2.py`.

---

## 5. Technical Debt & Future Roadmap

*   **Watchdog Implementations:** Introduce hardware watchdogs to reset the system if scheduled tasks hang.
*   **Version 3.0 Handoff:** Prepared structural modules to support Computer Vision (image sensors and frame processing loops) without modifying frozen code layers.
