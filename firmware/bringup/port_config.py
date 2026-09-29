"""
AquaSentinel-AI: Authoritative Development Serial Port Configuration
====================================================================
Parallel USB Port Assignment:
  - MAIN_ESP32_PORT : COM3 (NodeMCU ESP-32S / Silicon Labs CP210x)
  - ESP32_CAM_PORT  : COM4 (AI-Thinker ESP32-CAM / WCH CH340 on ESP32-CAM-MB)

Both boards operate simultaneously in the development environment.
"""

import os
import sys

# Authoritative Fixed Port Definitions
MAIN_ESP32_PORT = os.environ.get("MAIN_ESP32_PORT", "COM3")
ESP32_CAM_PORT = os.environ.get("ESP32_CAM_PORT", "COM4")


def get_main_esp32_port(default: str = MAIN_ESP32_PORT) -> str:
    """Returns the serial port for Main ESP32, allowing CLI arg or env override."""
    for arg in sys.argv[1:]:
        if arg.upper().startswith("COM") or "/dev/" in arg:
            return arg
    return os.environ.get("MAIN_ESP32_PORT", default)


def get_esp32_cam_port(default: str = ESP32_CAM_PORT) -> str:
    """Returns the serial port for ESP32-CAM, allowing CLI arg or env override."""
    for arg in sys.argv[1:]:
        if arg.upper().startswith("COM") or "/dev/" in arg:
            return arg
    return os.environ.get("ESP32_CAM_PORT", default)
