# VERSION 4.8.4 — DEPLOYMENT CONFIGURATION, SECURITY, DEPENDENCY & RELEASE INTEGRITY AUDIT

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** V4.8.4 Forensic Configuration, Security & Dependency Audit  
**Audit Date:** August 18, 2026  
**Status:** Phase 1 Forensic Configuration Audit Complete (Zero Source Code Modifications)

---

## Executive Summary

Phase 1 of Milestone V4.8.4 presents a forensic audit across configuration files, environment variables, secrets/credentials, Python dependency declarations, PyTorch CV model metadata, and system release manifests.

The audit identified key configuration discrepancies, hardcoded plaintext secrets in configuration headers, incomplete Python dependency declarations in `requirements.txt`, and an outdated `release_manifest.json` frozen at V3.0.

---

## 1. Forensic Audit Discrepancies & Conflict Findings

### 1.1 GPIO / Pin Mapping Discrepancy
- **Authoritative Baseline (V4.8.1 Resolved Mapping)**:
  - Temperature: `GPIO 18`
  - pH Probe: `GPIO 32`
  - Turbidity: `GPIO 33`
  - DO Probe: `GPIO 34`
  - Salinity / TDS: `GPIO 36`
  - Green LED: `GPIO 19`
  - Yellow LED: `GPIO 21`
  - Red LED: `GPIO 22`
  - Buzzer: `GPIO 23`
  - Pump Relay: `GPIO 27`
  - GPS RX: `GPIO 16`, GPS TX: `GPIO 17`
- **Config Conflict in `config/device_config.json`**:
  - `green_led`: 12 (Conflict with MTDI strapping pin)
  - `yellow_led`: 13
  - `red_led`: 14
  - `buzzer`: 15 (Conflict with MTDO strapping pin)
  - `pump_relay`: 16 (Conflict with GPS RX)
  - `gps`: 21 (Conflict with Yellow LED)
  - `rtc`: 22 (Conflict with Red LED)
- **Discrepancy Severity**: 🔴 **HIGH**. `config/device_config.json` retains outdated pre-V4.8.1 pin mapping.

### 1.2 Plaintext Secrets & Credential Exposure
- **Finding in `config/device_config.json`**: Lines 8–9 and 69–70 contain hardcoded plaintext Wi-Fi AP credentials:
  - `ssid`: `"AquaNet_Freshwater_AP"`, `"password": "aquasentinel_secure"`
- **Finding in `firmware/esp32_cam/main_esp32_cam.cpp`**: Lines 42–43 contain hardcoded Wi-Fi credentials:
  - `WIFI_SSID = "AquaNet_Freshwater_AP"`, `WIFI_PASS = "aquasentinel_secure"`
- **Finding in `firmware/src/main.cpp`**: Lines 88 contain hardcoded MQTT broker credentials:
  - `MQTTConfig mqttConfig = {"broker.hivemq.com", 1883, ... "user", "pass"}`
- **Discrepancy Severity**: 🔴 **HIGH**. Secrets are hardcoded in tracked repository configuration and firmware files. Lack of `.env.example` placeholder template.

### 1.3 Missing Production Python Dependencies
- **Audit of `requirements.txt`**:
  - Declares: `pandas`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn`, `pyyaml`, `openpyxl`, `fastapi`, `uvicorn`, `paho-mqtt`, `jinja2`, `ipykernel`, `joblib`, `streamlit`, `websockets`, `pydantic`.
  - **MISSING DECLARED PACKAGES**:
    1. `torch` (PyTorch - required for `AquaticBloomCVModel`)
    2. `torchvision` (required for MobileNetV3 image transforms)
    3. `Pillow` (PIL - required for `CameraFrame` and `ImagePreprocessor`)
    4. `opencv-python` (cv2 - required for visual processing)
    5. `scipy` (required for statistical processing)
  - All declared packages currently use un-pinned `>=` version specifiers.
- **Discrepancy Severity**: 🔴 **HIGH**. PyTorch and CV dependencies are completely omitted from `requirements.txt`.

### 1.4 Model Artifact & Metadata Audit
- **Model Checkpoint**: [models/cv/aquatic_bloom_mobilenetv3.pt](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/models/cv/aquatic_bloom_mobilenetv3.pt) (5.93 MB / 6,218,731 bytes).
- **Metadata Checkpoint**: [models/cv/aquatic_bloom_model_metadata.json](file:///p:/5th%20semester/Embedded%20Systems/Capstone%20Project/models/cv/aquatic_bloom_model_metadata.json).
- **Verification**: Model architecture (`mobilenet_v3_small`), classes (`["NORMAL_WATER", "ALGAL_BLOOM", "TURBID_DISCOLORATION"]`), input resolution (`224x224`), and color space (`RGB`) match V4.2 Preprocessor and V4.3 Model contracts.
- **Discrepancy Severity**: 🟢 **LOW / OK**. Model weights and metadata are intact. SHA-256 hash checksum needs to be calculated and recorded in release manifest.

### 1.5 Release Manifest Outdated State
- **Audit of `config/release_manifest.json`**:
  - `release_version`: `"1.0.0"` (Outdated, frozen at V3.0 state).
  - `test_count`: `180` (Outdated; current test baseline is 275 pytest items / 244 core assertions).
  - `active_ml_models`: Lists only `caml` and `habsos` tabular models. Missing CV MobileNetV3 model (`aquatic_bloom_mobilenetv3.pt`).
  - Missing V4.1–V4.8.3 completed milestone declarations.
- **Discrepancy Severity**: 🟠 **MEDIUM**. Release manifest does not reflect current V4 capabilities.

---

## 2. Configuration Hierarchy Design (Phase 2–10 Plan)

To resolve these audit findings in Phase 2–10:

1. **Hierarchy Division**:
   - **Hardware Config**: `config/device_config.json` & `firmware/include/config/PinConfig.h` $\rightarrow$ Updated to V4.8.1 Authoritative Pin Mapping.
   - **Network & Secrets**: Environment variables (`AQUA_WIFI_SSID`, `AQUA_WIFI_PASS`, `AQUA_MQTT_HOST`, `AQUA_MQTT_USER`, `AQUA_MQTT_PASS`) with `.env.example` template.
   - **Model Config & Integrity**: SHA-256 integrity checksum calculated and pinned in `aquatic_bloom_model_metadata.json` and `release_manifest.json`.
   - **Dependencies**: Explicitly add `torch`, `torchvision`, `Pillow`, `opencv-python`, `scipy` to `requirements.txt` with pinned/controlled version specifiers.
   - **Release Manifest**: Update `config/release_manifest.json` to version `4.8.4`, listing all V4 milestones, model artifacts, test baselines, and `PHYSICAL_HARDWARE_VALIDATION: PENDING`.
   - **Startup Validator**: Create `src/config/deployment_validator.py` verifying GPIO maps, sampling intervals, secrets, dependencies, model SHA-256 checksums, and temporal thresholds.

---

## 3. Audit Verification Summary

| Component / Artifact | Current Status | Required Action for V4.8.4 | Severity |
| :--- | :--- | :--- | :--- |
| **`device_config.json` GPIO** | Pre-V4.8.1 Outdated Map | Align with V4.8.1 Authoritative Map | 🔴 HIGH |
| **Wi-Fi & MQTT Credentials** | Plaintext Hardcoded | Move to Environment Variables / `.env.example` | 🔴 HIGH |
| **`requirements.txt`** | Missing PyTorch & OpenCV | Add `torch`, `torchvision`, `Pillow`, `opencv-python`, `scipy` | 🔴 HIGH |
| **`release_manifest.json`** | Frozen at V3.0 (v1.0.0) | Update to V4.8.4, add PyTorch model SHA-256 | 🟠 MEDIUM |
| **Startup Configuration Validator**| Missing | Create `src/config/deployment_validator.py` | 🟠 MEDIUM |
| **V3.8 Frozen Source Files** | 0 Modifications | Maintain 100% untouched protection | 🟢 CLEAN |
