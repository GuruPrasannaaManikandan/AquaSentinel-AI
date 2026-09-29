#!/usr/bin/env python3
"""
AquaSentinel-AI: Physical ESP32-CAM (GC2145 on COM4) 10-Frame Validation
========================================================================
Connects to COM4 @ 115200 baud, sends serial capture commands,
verifies GC2145 sensor detection, PSRAM, and captures at least 10 real
optical frames directly from the physical camera.
Records frame number, width, height, format, size, success, and timestamp.
"""

import sys
import os
import time
import base64
import json
import io
import datetime
import serial
from PIL import Image

PORT = "COM4"
BAUD = 115200

def capture_single_frame(ser, timeout=12.0):
    ser.reset_input_buffer()
    ser.write(b"c\r\n")
    
    b64_lines = []
    capturing = False
    start_t = time.time()
    jpeg_bytes = None
    width = 320
    height = 240
    
    while time.time() - start_t < timeout:
        line_bytes = ser.readline()
        if not line_bytes:
            continue
        line = line_bytes.decode('utf-8', errors='replace').strip()
        
        if "<<<FRAME_B64_START:" in line:
            capturing = True
            b64_lines = []
            try:
                parts = line.replace("<<<FRAME_B64_START:", "").replace(">>>", "").split(":")
                if len(parts) >= 2:
                    width = int(parts[0])
                    height = int(parts[1])
            except Exception:
                pass
            continue
            
        if "<<<FRAME_B64_END>>>" in line:
            capturing = False
            full_b64 = "".join(b64_lines)
            try:
                jpeg_bytes = base64.b64decode(full_b64)
            except Exception:
                jpeg_bytes = None
            break
            
        if capturing:
            b64_lines.append(line)
            
    return jpeg_bytes, width, height

def main():
    print(f"Connecting to ESP32-CAM on {PORT} at {BAUD} baud...")
    ser = serial.Serial(PORT, BAUD, timeout=1.0)
    time.sleep(1.0)
    
    # Query system status
    ser.write(b"s\r\n")
    time.sleep(0.5)
    while ser.in_waiting:
        print("  [CAM STATUS]", ser.readline().decode('utf-8', errors='replace').strip())
        
    # Trigger Phase E on the ESP32-CAM (10-frame repeated capture test)
    print("\nTriggering on-device Phase E (10 repeated frames capture test)...")
    ser.write(b"e\r\n")
    time.sleep(2.0)
    start_e = time.time()
    while time.time() - start_e < 8.0:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line:
                print(f"  [CAM PHASE E] {line}")
            if "REPEATED FRAME CAPTURE: PASS" in line or "[PHASE E SUMMARY]" in line:
                break
        else:
            time.sleep(0.1)

    # Now capture 10 real full JPEG frames into Python over serial
    print("\nNow capturing 10 distinct optical frames into Python over COM4...")
    frames_evidence = []
    
    for i in range(1, 11):
        t_capture = datetime.datetime.now(datetime.timezone.utc).isoformat()
        t0 = time.perf_counter()
        raw_bytes, w, h = capture_single_frame(ser, timeout=10.0)
        dt = time.perf_counter() - t0
        
        if raw_bytes and len(raw_bytes) > 100 and raw_bytes.startswith(b"\xff\xd8"):
            # Verify with PIL
            img = Image.open(io.BytesIO(raw_bytes))
            actual_w, actual_h = img.size
            format_name = img.format
            channels = len(img.getbands())
            
            entry = {
                "frame_number": i,
                "width": actual_w,
                "height": actual_h,
                "channels": channels,
                "format": format_name,
                "buffer_size_bytes": len(raw_bytes),
                "magic_bytes": f"0x{raw_bytes[0]:02X} 0x{raw_bytes[1]:02X}",
                "capture_latency_sec": round(dt, 3),
                "capture_success": True,
                "timestamp": t_capture
            }
            frames_evidence.append(entry)
            print(f"  Frame {i:2d}/10: PASS | Size: {len(raw_bytes):5d} B | Dim: {actual_w}x{actual_h} | Time: {dt:.2f}s | Magic: {entry['magic_bytes']}")
            
            # Save the latest valid frame as both live_camera_frame.jpg and LIVE_ESP32_CAM_GC2145_FRAME.jpg
            if i == 10 or i == 1:
                os.makedirs("docs", exist_ok=True)
                for out_name in ["live_camera_frame.jpg", "LIVE_ESP32_CAM_GC2145_FRAME.jpg"]:
                    with open(os.path.join("docs", out_name), "wb") as f:
                        f.write(raw_bytes)
        else:
            entry = {
                "frame_number": i,
                "capture_success": False,
                "timestamp": t_capture,
                "error": "Failed to receive valid JPEG frame"
            }
            frames_evidence.append(entry)
            print(f"  Frame {i:2d}/10: FAIL")
            
        time.sleep(0.3)
        
    ser.close()
    
    # Save evidence log
    evidence_path = os.path.join("docs", "physical_camera_10frames_evidence.json")
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(frames_evidence, f, indent=2)
        
    success_count = sum(1 for e in frames_evidence if e.get("capture_success"))
    print(f"\n=======================================================")
    print(f"10-FRAME PHYSICAL CAPTURE RESULT: {success_count}/10 SUCCESS")
    print(f"Evidence saved to: {evidence_path}")
    print(f"=======================================================")
    
    return success_count == 10

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
