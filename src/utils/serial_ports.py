"""
AquaSentinel-AI: serial port discovery for the two USB-connected boards.

Port numbers change between laptops and USB sockets (COM3/COM4 on the original
bench, COM7 on another laptop), so nothing should hardcode them. Resolution order:

1. Environment variable: AQUA_MAIN_PORT (sensor ESP32) / AQUA_CAM_PORT (ESP32-CAM).
   The older names MAIN_ESP32_PORT / ESP32_CAM_PORT are honoured too.
2. Probing: every serial port is opened read-only for a few seconds with
   DTR/RTS released (so neither board is reset) and identified by what it prints.
   The main firmware prints "[TELEMETRY-JSON]" / "[HAL-ALL]"; the camera firmware
   prints "[HEARTBEAT]" / "ESP32-CAM".
3. USB chip as a last resort: CH340 (VID 0x1A86) is the ESP32-CAM-MB base board,
   CP210x (VID 0x10C4) is the usual NodeMCU/DevKit sensor board.

Usage:  python -m src.utils.serial_ports      (prints what it finds)
"""

import os
import time
from typing import Dict, List, Optional

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - pyserial is in requirements
    serial = None
    list_ports = None

MAIN = "main"
CAM = "cam"

_ENV_NAMES = {
    MAIN: ("AQUA_MAIN_PORT", "MAIN_ESP32_PORT"),
    CAM: ("AQUA_CAM_PORT", "ESP32_CAM_PORT"),
}

_SIGNATURES = {
    MAIN: ("[TELEMETRY-JSON]", "[HAL-ALL]", "[PH-DRIVER]", "[TURBIDITY-DRIVER]", "AquaSentinel-AI Firmware", "[TASK]", "[CMD]"),
    CAM: ("[HEARTBEAT]", "ESP32-CAM", "<<<FRAME_B64", "CAMERA INITIALIZATION", "[STATUS] Free Heap"),
}

_USB_VIDS = {
    CAM: (0x1A86,),          # WCH CH340 on the ESP32-CAM-MB programmer
    MAIN: (0x10C4, 0x0403),  # Silicon Labs CP210x, FTDI
}

_cache: Dict[str, Optional[str]] = {}


def _env_port(role: str) -> Optional[str]:
    for name in _ENV_NAMES[role]:
        val = os.environ.get(name)
        if val:
            return val.strip()
    return None


def list_serial_ports() -> List[dict]:
    if list_ports is None:
        return []
    out = []
    for p in list_ports.comports():
        out.append({
            "device": p.device,
            "description": p.description,
            "vid": p.vid,
            "pid": p.pid,
            "hwid": p.hwid,
        })
    return out


def open_port(port: str, baud: int = 115200, timeout: float = 1.0):
    """Opens a port without toggling DTR/RTS, so the board is not reset."""
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baud
    ser.timeout = timeout
    ser.dtr = False
    ser.rts = False
    ser.open()
    return ser


def identify_port(port: str, listen_sec: float = 4.0, baud: int = 115200) -> Optional[str]:
    """Listens on a port and returns MAIN, CAM or None based on its output."""
    if serial is None:
        return None
    try:
        ser = open_port(port, baud, timeout=0.3)
    except Exception:
        return None  # busy (another program holds it) or not a real port
    try:
        deadline = time.time() + listen_sec
        sent_probe = False
        while time.time() < deadline:
            line = ser.readline().decode("utf-8", errors="replace")
            for role, sigs in _SIGNATURES.items():
                if any(sig in line for sig in sigs):
                    return role
            # Quiet board: both firmwares answer a harmless command.
            if not sent_probe and time.time() > deadline - listen_sec / 2:
                ser.write(b"s\n")   # camera: status line ('s'); main: "[CMD] Unknown command"
                sent_probe = True
        return None
    finally:
        try:
            ser.close()
        except Exception:
            pass


def find_port(role: str, probe: bool = True, use_cache: bool = True) -> Optional[str]:
    """Returns the COM port for MAIN or CAM, or None if it cannot be found."""
    env = _env_port(role)
    if env:
        return env
    if use_cache and _cache.get(role):
        return _cache[role]

    ports = list_serial_ports()
    found: Optional[str] = None

    if probe:
        other = CAM if role == MAIN else MAIN
        for p in ports:
            if _cache.get(other) == p["device"]:
                continue
            ident = identify_port(p["device"])
            if ident:
                _cache[ident] = p["device"]
            if ident == role:
                found = p["device"]
                break

    if not found:
        candidates = [p for p in ports if p["vid"] in _USB_VIDS[role]]
        if len(candidates) == 1:
            found = candidates[0]["device"]

    if found:
        _cache[role] = found
    return found


def forget(role: str) -> None:
    _cache.pop(role, None)


if __name__ == "__main__":
    print("Serial ports:")
    for p in list_serial_ports():
        vid = f"{p['vid']:04X}" if p["vid"] is not None else "----"
        pid = f"{p['pid']:04X}" if p["pid"] is not None else "----"
        print(f"  {p['device']:<12} VID:PID={vid}:{pid}  {p['description']}")
    print()
    print(f"Sensor ESP32 (turbidity/pH): {find_port(MAIN) or 'NOT FOUND'}")
    print(f"ESP32-CAM                  : {find_port(CAM) or 'NOT FOUND'}")
    print("Override with AQUA_MAIN_PORT / AQUA_CAM_PORT, e.g.  set AQUA_MAIN_PORT=COM7")
