import serial
import time
import sys

try:
    ser = serial.Serial('COM3', 115200, timeout=1)
    print("Opened COM3 at 115200 baud")
    time.sleep(1)
    # Send newline or toggle DTR/RTS if needed
    start_time = time.time()
    while time.time() - start_time < 12:
        line = ser.readline()
        if line:
            try:
                print(line.decode('utf-8', errors='replace').rstrip())
            except Exception as e:
                print(f"Decode error: {e}")
    ser.close()
    print("Monitor finished")
except Exception as e:
    print(f"Error opening serial port: {e}")
    sys.exit(1)
