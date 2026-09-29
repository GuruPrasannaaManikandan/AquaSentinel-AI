#!/usr/bin/env python3
"""
AquaSentinel-AI: Live ESP32-CAM (GC2145) Bridge Daemon
======================================================
Interfaces with physical ESP32-CAM on COM4 at 115200 baud,
triggers periodic frame capture via 'c' command,
receives Base64 JPEG frame, validates magic bytes (0xFF 0xD8),
saves the latest physical frame to docs/LIVE_ESP32_CAM_GC2145_FRAME.jpg,
and posts the frame to FastAPI backend (POST /devices/{device_id}/frame)
for optical quality evaluation (Q_visual) and aquatic bloom classification.
"""

import sys
import os
import time
import base64
import json
import urllib.request
import serial

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = "COM4"
BAUD = 115200
DEVICE_ID = "AQUA_FRESH_001"
BACKEND_URL = f"http://127.0.0.1:8000/devices/{DEVICE_ID}/frame"
DOCS_IMG_PATH = os.path.join(BASE_DIR, "docs", "LIVE_ESP32_CAM_GC2145_FRAME.jpg")

def capture_frame(port=PORT, baud=BAUD, timeout=12.0):
    """Sends 'c' command to COM4 and reads Base64 JPEG frame."""
    ser = serial.Serial(port, baud, timeout=1.0)
    time.sleep(0.5)
    ser.reset_input_buffer()
    
    ser.write(b"c\r\n")
    b64_lines = []
    capturing = False
    start_t = time.time()
    jpeg_bytes = None
    
    while time.time() - start_t < timeout:
        line_bytes = ser.readline()
        if not line_bytes:
            continue
        line = line_bytes.decode('utf-8', errors='replace').strip()
        
        if "<<<FRAME_B64_START:" in line:
            capturing = True
            b64_lines = []
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
            
    ser.close()
    return jpeg_bytes

def post_frame_to_backend(jpeg_bytes, frame_id=None):
    """Encodes frame and POSTs to backend."""
    b64_str = base64.b64encode(jpeg_bytes).decode('ascii')
    fid = frame_id or f"cam4_frame_{int(time.time() * 1000)}"
    payload = {
        "image_base64": b64_str,
        "format": "JPEG",
        "frame_id": fid,
        "width": 320,
        "height": 240
    }
    
    req = urllib.request.Request(
        BACKEND_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=5.0) as resp:
        return json.loads(resp.read().decode('utf-8'))

def run_single():
    print(f"[LIVE-CAM-BRIDGE] Connecting to ESP32-CAM on {PORT}...")
    try:
        raw_frame = capture_frame()
        if raw_frame and len(raw_frame) > 100 and raw_frame.startswith(b"\xff\xd8"):
            print(f"[LIVE-CAM-BRIDGE] Captured {len(raw_frame)} bytes JPEG from COM4 GC2145.")
            os.makedirs(os.path.dirname(DOCS_IMG_PATH), exist_ok=True)
            with open(DOCS_IMG_PATH, "wb") as f:
                f.write(raw_frame)
            print(f"[LIVE-CAM-BRIDGE] Saved frame to {DOCS_IMG_PATH}")
            
            res = post_frame_to_backend(raw_frame)
            print(f"[LIVE-CAM-BRIDGE] Backend Ingestion SUCCESS:")
            print(f"   Visual State: {res.get('evidence_state')}")
            print(f"   Q_visual: {res.get('q_visual')}")
            print(f"   Effective Conf: {res.get('effective_confidence')}")
            return True
        else:
            print("[LIVE-CAM-BRIDGE] Failed to capture valid frame from COM4.")
            return False
    except Exception as e:
        print(f"[LIVE-CAM-BRIDGE] Error during capture: {e}")
        return False

def run_loop(interval_sec=10.0):
    print(f"[LIVE-CAM-BRIDGE] Starting daemon loop (interval={interval_sec}s)...")
    while True:
        try:
            run_single()
        except Exception as e:
            print(f"[LIVE-CAM-BRIDGE] Loop iteration error: {e}")
        time.sleep(interval_sec)

if __name__ == "__main__":
    if "--loop" in sys.argv:
        run_loop()
    else:
        success = run_single()
        sys.exit(0 if success else 1)
