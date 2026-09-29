import time
import serial

print("Checking COM4 (ESP32-CAM with GC2145 sensor)...")
try:
    ser = serial.Serial("COM4", 115200, timeout=3.0)
    print("Opened COM4 successfully. Reading lines for 5 seconds...")
    t_end = time.time() + 5.0
    lines = []
    while time.time() < t_end:
        line = ser.readline().decode('utf-8', errors='replace').strip()
        if line:
            print(f"  [COM4] {line}")
            lines.append(line)
    ser.close()
    if not lines:
        print("  [COM4] No text received over UART (camera may be running WiFi webserver or waiting).")
except Exception as e:
    print(f"  [COM4] Error or port in use: {e}")
