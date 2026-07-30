# Build & Deployment Guide

This guide details how to set up the build environment, compile the AquaSentinel-AI firmware, flash the binary to an ESP32 board, and monitor its serial outputs.

## Required Tools

1. **PlatformIO CLI / Core**: Standard build system for compiling ESP32 configurations.
2. **Python (3.10+)**: Required for running build configurations and simulation test runners.
3. **CP210x USB to UART Bridge Driver**: Necessary to detect physical ESP32 boards on the serial COM ports.

## Build Commands

Navigate to the `firmware/` directory and run:

```bash
# Clean previous builds
pio run --target clean

# Compile the firmware
pio run
```

## Flash and Upload Commands

To compile and upload the binary to an ESP32 connected via USB:

```bash
# Upload to target board (auto-detects port)
pio run --target upload

# Upload targeting a specific COM port
pio run --target upload --upload-port COM3
```

## Serial Monitor Commands

To open the serial console and view diagnostics, self-test summaries, and task feeds:

```bash
# Open serial monitor (default baud rate: 115200)
pio device monitor

# Open monitor on a specific port with specific baud rate
pio device monitor -p COM3 -b 115200
```

## Troubleshooting

- **Target board not found**: Make sure the ESP32 bridge driver is installed and the cable supports data lines.
- **Port Permission Denied**: Close other serial monitor windows before flashing.
- **Compiler errors (Missing headers)**: Run `pio lib install` to restore dependencies defined in `platformio.ini`.
