# VERSION 4.8.4 — DEPLOYMENT CONFIGURATION, SECURITY, DEPENDENCY & RELEASE INTEGRITY

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** V4.8.4 Deployment Configuration & Security Implementation  
**Completion Date:** August 18, 2026  
**Verified Test Baseline:** 299 passed, 3 skipped (302 total pytest items), 244/244 Phase 9 core assertions  
**V3.8 Source Code Modifications:** ZERO (0) (Verified via `git status`)

---

## Executive Summary

Version 4.8.4 completes the software-first physical-deployment preparation by establishing a single source of truth configuration hierarchy, secret security (.env.example), explicit Python dependency declarations (`torch`, `torchvision`, `Pillow`, `opencv-python`, `scipy`), PyTorch MobileNetV3 model SHA-256 integrity verification, release manifest synchronization, and a safe 10-step startup deployment validator.

---

## 1. Single Source of Truth Configuration Hierarchy

The deployment configuration is structured into isolated, authoritative layers:

1. **Hardware Configuration**: [config/device_config.json](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/config/device_config.json) & [firmware/include/config/PinConfig.h](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/firmware/include/config/PinConfig.h). Synchronized to the V4.8.1 Authoritative Pin Mapping.
2. **Secrets & Security**: [.env.example](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/.env.example). Environment variable placeholders (`AQUA_WIFI_SSID`, `AQUA_WIFI_PASSWORD`, `AQUA_MQTT_HOST`, `AQUA_MQTT_USERNAME`, `AQUA_MQTT_PASSWORD`). Plaintext secrets removed from code.
3. **Model Configuration & Integrity**: [models/cv/aquatic_bloom_model_metadata.json](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/models/cv/aquatic_bloom_model_metadata.json). SHA-256 checksum pinned: `19d84e0b1d27571296591434e02ec9331f14a49c75680f57c73333e7e53bb6bb`.
4. **Dependency Declarations**: [requirements.txt](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/requirements.txt). Explicitly lists `torch>=2.0.0`, `torchvision>=0.15.0`, `Pillow>=9.5.0`, `opencv-python>=4.7.0`, `scipy>=1.10.0`.
5. **Release Manifest**: [config/release_manifest.json](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/config/release_manifest.json). Updated to version `4.8.4` with test baseline 275 and `physical_hardware_validation: "PENDING"`.

---

## 2. Authoritative Hardware GPIO Pin Mapping

```
                       ESP32-WROOM-32 Pinout Assignment
                          +───────────────────────+
                          |                       |
       [ DS18B20 Temp ] ──| GPIO 18         3.3V  |── [ 3.3V Power Rail ]
       [ pH Probe ] ──────| GPIO 32 (ADC1)  5.0V  |── [ 5.0V Power Rail ]
       [ Turbidity ] ─────| GPIO 33 (ADC1)  GND   |── [ Ground Rail ]
       [ DO Probe ] ──────| GPIO 34 (ADC1)  GPIO27|── [ Pump Relay ]
       [ Salinity / TDS ]─| GPIO 36 (ADC1)  GPIO23|── [ Alarm Buzzer ]
       [ GPS RX ] ────────| GPIO 16         GPIO22|── [ Red LED ]
       [ GPS TX ] ────────| GPIO 17         GPIO21|── [ Yellow LED ]
                          |                 GPIO19|── [ Green LED ]
                          +───────────────────────+
```

---

## 3. Safe 10-Step Startup Validation Sequence

Module: [src/config/deployment_validator.py](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/src/config/deployment_validator.py)

1. Load Device Configuration
2. Validate GPIO Pin Mapping & Collision Check
3. Validate Sampling & Camera Capture Intervals
4. Validate PyTorch Model Checkpoint File Existence
5. Validate PyTorch Model SHA-256 Checksum (`19d84e0b1d27571296591434e02ec9331f14a49c75680f57c73333e7e53bb6bb`)
6. Audit Secret Safety & Credentials
7. Validate V4.8.3 Temporal Thresholds
8. Validate MQTT Broker & Network Topics
9. Initialize Logging & Component Pipeline
10. Confirm System Readiness / Halted Status

---

## 4. Frozen V3.8 Source Protection

Empirical verification via `git status --porcelain`:
- `src/iot/esp32_device.py`: **UNTOUCHED (0 modifications)**
- `src/iot/communication.py`: **UNTOUCHED (0 modifications)**
- `src/iot/scheduler.py`: **UNTOUCHED (0 modifications)**
- `src/iot/hal.py`: **UNTOUCHED (0 modifications)**
- `src/iot/actuators.py`: **UNTOUCHED (0 modifications)**
