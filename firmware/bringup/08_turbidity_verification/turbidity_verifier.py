"""
turbidity_verifier.py
Host companion runner for Turbidity Sensor Hardware Verification (Stage 08)
Connects to MAIN ESP32 on COM3 @ 115200 baud, coordinates test protocols for
Phases T3–T8, logs all measurements, and performs statistical analysis.
"""

import os
import sys
import time
import serial
import numpy as np

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
TIMEOUT = 1.0

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "reports", "turbidity_verification")
OUTPUT_DIR = os.path.abspath(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(OUTPUT_DIR, "turbidity_verification_log.txt")


class TurbidityVerifier:
    def __init__(self, port=PORT, baud=BAUD):
        self.port = port
        self.baud = baud
        self.s = None
        self.logs = []

    def connect(self):
        print(f"[STATUS] Connecting to {self.port} @ {self.baud} baud...", flush=True)
        self.s = serial.Serial(self.port, self.baud, timeout=TIMEOUT)
        time.sleep(1.5)  # Wait for boot banner
        print(f"[STATUS] Connected to {self.port}.", flush=True)

    def close(self):
        if self.s and self.s.is_open:
            self.s.close()
            print("[STATUS] Serial connection closed.", flush=True)
        # Save log file
        with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(self.logs))
        print(f"[SAVED] Verification session log written to: {LOG_FILE_PATH}", flush=True)

    def read_lines(self, duration_sec=6.0, echo=True):
        lines = []
        start = time.time()
        while time.time() - start < duration_sec:
            raw = self.s.readline()
            if raw:
                line = raw.decode("utf-8", errors="replace").strip()
                if line:
                    lines.append(line)
                    self.logs.append(line)
                    if echo:
                        print(f"  {line}", flush=True)
        return lines

    def send_cmd(self, cmd_char, duration_sec=6.0, echo=True):
        self.s.reset_input_buffer()
        cmd_bytes = f"{cmd_char}\n".encode("utf-8")
        self.s.write(cmd_bytes)
        return self.read_lines(duration_sec=duration_sec, echo=echo)


def main():
    print("==================================================================", flush=True)
    print("   AquaSentinel-AI: Turbidity Sensor Verification Tool", flush=True)
    print(f"   Target Port: {PORT} @ {BAUD} baud", flush=True)
    print(f"   Output Directory: {OUTPUT_DIR}", flush=True)
    print("==================================================================", flush=True)

    v = TurbidityVerifier()
    v.connect()

    # Initial flush & read banner
    print("\n[STEP 1] Reading initial boot and circuit configuration...", flush=True)
    v.read_lines(duration_sec=3.0)

    v.close()


if __name__ == "__main__":
    main()
