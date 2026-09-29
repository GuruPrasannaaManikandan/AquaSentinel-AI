"""
live_monitor.py
Real-time high-speed ADC and voltage monitor on COM3 for turbidity trimpot tuning.
Prints instantaneous ADC counts, V_P34, and estimated V_OUT.
"""

import os
import sys
import time
import serial

# Centralized Port Configuration (COM3 for Main ESP32)
try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from port_config import get_main_esp32_port
    PORT = get_main_esp32_port("COM3")
except Exception:
    PORT = os.environ.get("MAIN_ESP32_PORT", "COM3")
    if len(sys.argv) > 1 and sys.argv[1].upper().startswith("COM"):
        PORT = sys.argv[1]

BAUD = 115200

def main():
    print("==================================================================", flush=True)
    print("   AquaSentinel Turbidity Sensor — Real-Time Live Monitor", flush=True)
    print(f"   Target Port: {PORT} @ {BAUD} baud", flush=True)
    print("   Press Ctrl+C to exit.", flush=True)
    print("==================================================================", flush=True)

    try:
        s = serial.Serial(PORT, BAUD, timeout=0.5)
    except Exception as e:
        print(f"[ERROR] Could not open {PORT}: {e}")
        return

    time.sleep(1.0)
    s.reset_input_buffer()

    try:
        while True:
            raw = s.readline()
            if raw:
                line = raw.decode("utf-8", errors="replace").strip()
                if line and "[WINDOW" in line:
                    print(f"  {line}", flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        s.close()
        print("\n[STATUS] Live monitor stopped.", flush=True)

if __name__ == "__main__":
    main()
