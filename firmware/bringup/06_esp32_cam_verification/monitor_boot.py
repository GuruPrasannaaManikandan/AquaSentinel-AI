"""
Phase 6 / Step 3: ESP32-CAM Reset Boot Log Diagnostic Script
Target: COM4 @ 115200 baud
Monitors incoming bytes, records timestamps, and prints hex/ASCII representation.
"""
import os
import sys
import time
import serial

# Centralized Port Configuration (COM4 for ESP32-CAM)
try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from port_config import get_esp32_cam_port
    PORT = get_esp32_cam_port("COM4")
except Exception:
    PORT = os.environ.get("ESP32_CAM_PORT", "COM4")
    if len(sys.argv) > 1 and sys.argv[1].upper().startswith("COM"):
        PORT = sys.argv[1]

BAUD = 115200
DURATION = 45  # seconds


def main():
    print(f"==================================================================")
    print(f"   AquaSentinel-AI: ESP32-CAM Reset Boot Log Capture")
    print(f"   Target Port: {PORT} @ {BAUD} baud | Duration: {DURATION}s")
    print(f"==================================================================")
    
    try:
        # Open serial port without hardware flow control
        s = serial.Serial(PORT, BAUD, timeout=0.1, rtscts=False, dsrdtr=False)
    except Exception as e:
        print(f"[ERROR] Failed to open {PORT}: {e}")
        sys.exit(1)

    # Explicitly de-assert DTR and RTS so the CH340 does not hold EN or IO0 low
    s.dtr = False
    s.rts = False
    time.sleep(0.2)
    s.reset_input_buffer()
    
    print("[STATUS] Serial port opened successfully with DTR=False, RTS=False.")
    print("[STATUS] Listening for incoming serial traffic...")
    print("------------------------------------------------------------------")
    
    start_time = time.time()
    total_bytes = 0
    all_data = bytearray()
    
    while time.time() - start_time < DURATION:
        elapsed = time.time() - start_time
        remaining = DURATION - elapsed
        n = s.in_waiting
        if n > 0:
            chunk = s.read(n)
            total_bytes += len(chunk)
            all_data.extend(chunk)
            timestamp = f"{elapsed:05.2f}s"
            hex_str = " ".join(f"{b:02X}" for b in chunk)
            ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            print(f"[{timestamp}] +{len(chunk):3d} bytes | HEX: {hex_str} | ASCII: {ascii_str}")
        time.sleep(0.05)
        
    s.close()
    
    print("------------------------------------------------------------------")
    print(f"[CAPTURE COMPLETE] Total time: {DURATION}s | Total bytes: {total_bytes}")
    if total_bytes > 0:
        print(f"[RAW HEX]: {all_data.hex()}")
        print(f"[RAW ASCII DECODE]:\n{all_data.decode('utf-8', errors='replace')}")
    else:
        print("[RESULT]: NO ESP32 UART BOOT OUTPUT DETECTED (0 bytes received).")
    print("==================================================================")

if __name__ == "__main__":
    main()
