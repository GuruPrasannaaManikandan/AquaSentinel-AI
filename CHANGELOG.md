# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and adheres to Semantic Versioning.

---

## [2.4.0] - 2026-07-19
### Added
- Dynamic validation boundaries loaded from centralized config `device_config.json`.
- Unified `get_physical_bounds` helper in `DeviceConfig` manager.
- Programmatic System Acceptance Test validation script `tests/sat_verification_v2.py`.

### Fixed
- Fixed the alert log Streamlit UI bug where raw DeltaGenerator objects printed on screen.
- Removed unused imports (`datetime`, `time`, `pandas`, `numpy`) in testing suites to enforce code quality.

---

## [2.1.0] - 2026-07-19
### Added
- Standalone virtual embedded device executable script `embedded_device/main.py`.
- Network-ready capability in `MQTTClient` connecting via real `paho-mqtt` sockets.
- Integrated programmatic testing suite `tests/integration_test_v2.py` verifying disconnect recovery and hot-swappable drivers.

---

## [2.0.0] - 2026-07-18
### Added
- Hardware Abstraction Layer (HAL) coordinate interface.
- Priority-sorted tick-based task scheduler mimicking cooperative RTOS.
- Decoupled `BaseSensorDriver` and `BaseActuatorDriver` classes.
- Centralized configuration schema `config/device_config.json`.

---

## [1.0.0] - 2026-07-18
### Added
- Supervised ML models and Artificial Immune System (NSA) classifiers.
- Evidence Fusion Dempster-Shafer combining framework.
- Streamlit interactive client dashboard.
- FastAPI REST gateway service and SQLite persistence layer.
