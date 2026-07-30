# Firmware Package Structure

This document outlines the directory structure of the AquaSentinel-AI project and details the role of each directory.

## Directory Mapping

```text
Capstone Project/
├── assets/          # Static graphic resources, flowcharts, and media
├── configs/         # System settings, calibration files, and configurations
├── docs/            # Architecture specifications, API logs, and reports
├── examples/        # Setup codes, wiring diagrams, and test examples
├── firmware/        # Primary PlatformIO ESP32 C++ firmware codebase
│   ├── include/     # Header includes and Task IDs definitions
│   ├── lib/         # Subsystem C++ libraries (FSM, WiFi, Backend, etc.)
│   └── src/         # Main firmware loop code (main.cpp)
├── scripts/         # Production flash scripts and build automations
├── src/             # Virtual gateway Python services (gateway.py, app.py)
└── tests/           # 186 automated simulation test cases
```

## Directory Roles

1. **`firmware/`**: Houses the ESP32 PlatformIO project. It contains the modular libraries (HAL, Scheduler, WiFi, MQTT, Backend, Diagnostics, Verification) and the cooperative scheduler task loop inside `main.cpp`.
2. **`docs/`**: Includes architectural diagrams, sync policies, watchdog thresholds, API freeze matrices, and release plans.
3. **`tests/`**: Holds python unit/integration tests running the complete system simulation (validating data preprocessing, ML/AIS classifications, evidence-fusion rules, and telemetry routing).
4. **`src/` (Python side)**: Implements the simulated device, local mock broker, gateway evidence fusion pipeline, FastAPI server, and Streamlit dashboard.
5. **`configs/`**: Stores baseline calibration values, weights, and scale factors.
