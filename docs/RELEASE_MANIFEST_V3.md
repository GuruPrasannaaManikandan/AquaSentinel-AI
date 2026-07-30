# Release Manifest (Version 3)

This release manifest lists the properties, environment parameters, and dependencies of AquaSentinel-AI Firmware Version 3.

## Release Metadata

- **Firmware Version**: `3.0.0`
- **Release Date**: `2026-07-29`
- **Semantic Version**: `v3.0.0`
- **Supported Hardware**: ESP32-WROOM-32E (and simulated ESP32 boards)
- **Supported Sensors**: temperature (DS18B20 style), pH, Salinity, Turbidity, Dissolved Oxygen (DO)
- **Supported Communication**: Wi-Fi (802.11 b/g/n), MQTT (v3.1.1)

## Directory Structure

```text
firmware/
├── include/       # Global includes and task definitions
├── lib/           # Modularized subsystem libraries
│   ├── HAL/       # Hardware abstraction layer interface
│   ├── FSM/       # Edge validation state machine
│   ├── Scheduler/ # Cooperative task scheduler
│   ├── WiFi/      # Wi-Fi link connectivity service
│   ├── MQTT/      # MQTT communication service
│   ├── Backend/   # Cloud synchronizations gateway (V3.9)
│   ├── Diagnostics/ # Central fault diagnostics & watchdogs (V3.10)
│   └── Verification/# Bootup validation & test runners (V3.11)
└── src/           # Firmware entrypoint main.cpp
```

## Build Environment

- **Build Tool**: PlatformIO CLI / Core
- **Compiler Version**: GCC C++ `xtensa-esp32-elf-g++` (esp-idf toolkit)
- **Python Version**: `3.10.x` (or newer)
- **PlatformIO Version**: `^6.1.x`

## Core Library Dependencies

- **ArduinoJson**: `^6.21.3` (JSON serialization/deserialization)
- **PubSubClient**: `^2.8.0` (MQTT protocol implementation)

## Release Status

- **Status**: **RELEASED / PRODUCTION READY**
- **Validation**: Passed all 186 automated simulation test checks.
