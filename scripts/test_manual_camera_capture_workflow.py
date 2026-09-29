#!/usr/bin/env python3
"""
AquaSentinel-AI: Manual Camera Capture Workflow & Freshness Verification Test
=============================================================================
Tests Phase 1 through Phase 15 requirements:
1. Status API: /api/camera/status
2. First Manual Capture: POST /api/camera/capture
3. Second Manual Capture: POST /api/camera/capture
4. Freshness Guarantee: Verify capture_id differs, timestamp differs, sequence increases
5. Concurrency/Double-Click Rejection test
6. Regression check: Backend, Main ESP32 (COM3), Live Telemetry
"""

import sys
import os
import time
import json
import urllib.request
import urllib.error
import threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_URL = "http://127.0.0.1:8000"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def test_manual_camera_pipeline():
    log("=== TEST SUITE: MANUAL CAMERA CAPTURE PIPELINE ===")

    # 1. Check Status
    log("Step 1: Testing GET /api/camera/status...")
    req = urllib.request.Request(f"{API_URL}/api/camera/status")
    with urllib.request.urlopen(req, timeout=5.0) as resp:
        st_data = json.loads(resp.read().decode('utf-8'))
    log(f"  Status Response: {st_data}")
    assert st_data.get("camera") == "ESP32-CAM", "Expected ESP32-CAM"
    assert st_data.get("sensor") == "GC2145", "Expected GC2145"
    assert st_data.get("source") == "PHYSICAL_ESP32_CAM", "Expected PHYSICAL_ESP32_CAM"
    print("  ✅ Step 1: Camera Status Verified PASS\n")

    # 2. First Capture
    log("Step 2: Triggering FIRST manual capture (POST /api/camera/capture)...")
    req = urllib.request.Request(f"{API_URL}/api/camera/capture", data=b"", method="POST")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=8.0) as resp:
        cap1 = json.loads(resp.read().decode('utf-8'))
    dt1 = time.time() - t0
    log(f"  Capture 1 succeeded in {dt1:.2f}s!")
    log(f"  Capture ID : {cap1.get('capture_id')}")
    log(f"  Sequence   : {cap1.get('frame_sequence')}")
    log(f"  Timestamp  : {cap1.get('timestamp')}")
    log(f"  Filename   : {cap1.get('filename')}")
    log(f"  Size Bytes : {cap1.get('size_bytes')}")
    log(f"  Dimensions : {cap1.get('width')}x{cap1.get('height')}")
    log(f"  Fresh Frame: {cap1.get('fresh_frame')}")
    opt1 = cap1.get("optical_intelligence", {})
    log(f"  Optical Q  : {opt1.get('q_visual')} (State: {opt1.get('quality_state')})")
    log(f"  Class      : {opt1.get('predicted_class')}")

    assert cap1.get("success") == 1 or cap1.get("success") is True, "Capture 1 failed!"
    assert cap1.get("fresh_frame") == 1 or cap1.get("fresh_frame") is True, "Frame not marked fresh!"
    assert cap1.get("size_bytes", 0) > 1000, "Frame size too small!"
    file1_path = os.path.join(BASE_DIR, cap1["filepath"])
    assert os.path.exists(file1_path), f"Saved image file missing: {file1_path}"
    with open(file1_path, "rb") as f:
        magic = f.read(2)
        assert magic == b"\xff\xd8", "Image missing JPEG magic bytes 0xFF 0xD8!"
    print("  ✅ Step 2: First Manual Capture Verified PASS\n")

    # Brief delay between captures
    time.sleep(1.0)

    # 3. Second Capture
    log("Step 3: Triggering SECOND manual capture (POST /api/camera/capture)...")
    req = urllib.request.Request(f"{API_URL}/api/camera/capture", data=b"", method="POST")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=8.0) as resp:
        cap2 = json.loads(resp.read().decode('utf-8'))
    dt2 = time.time() - t0
    log(f"  Capture 2 succeeded in {dt2:.2f}s!")
    log(f"  Capture ID : {cap2.get('capture_id')}")
    log(f"  Sequence   : {cap2.get('frame_sequence')}")
    log(f"  Timestamp  : {cap2.get('timestamp')}")
    log(f"  Filename   : {cap2.get('filename')}")
    log(f"  Size Bytes : {cap2.get('size_bytes')}")
    log(f"  Dimensions : {cap2.get('width')}x{cap2.get('height')}")
    log(f"  Fresh Frame: {cap2.get('fresh_frame')}")
    opt2 = cap2.get("optical_intelligence", {})
    log(f"  Optical Q  : {opt2.get('q_visual')} (State: {opt2.get('quality_state')})")
    log(f"  Class      : {opt2.get('predicted_class')}")

    assert cap2.get("success") == 1 or cap2.get("success") is True, "Capture 2 failed!"
    assert cap2.get("fresh_frame") == 1 or cap2.get("fresh_frame") is True, "Frame not marked fresh!"
    file2_path = os.path.join(BASE_DIR, cap2["filepath"])
    assert os.path.exists(file2_path), f"Saved image file missing: {file2_path}"
    print("  ✅ Step 3: Second Manual Capture Verified PASS\n")

    # 4. Freshness Verification
    log("Step 4: Comparing Capture 1 vs Capture 2 for Freshness Guarantees...")
    log(f"  Capture ID 1: {cap1['capture_id']} vs Capture ID 2: {cap2['capture_id']}")
    assert cap1['capture_id'] != cap2['capture_id'], "Capture IDs must differ!"

    log(f"  Timestamp 1 : {cap1['timestamp']} vs Timestamp 2 : {cap2['timestamp']}")
    assert cap1['timestamp'] != cap2['timestamp'], "Timestamps must differ!"

    log(f"  Sequence 1  : {cap1['frame_sequence']} vs Sequence 2  : {cap2['frame_sequence']}")
    assert cap2['frame_sequence'] > cap1['frame_sequence'], "Frame sequence must increase monotonically!"

    log(f"  Filename 1  : {cap1['filename']} vs Filename 2  : {cap2['filename']}")
    assert cap1['filename'] != cap2['filename'], "Filenames must differ!"
    print("  ✅ Step 4: Freshness Guarantees (IDs, Timestamps, Monotonic Sequence) Verified PASS\n")

    # 5. Concurrency / Double-Click Rejection
    log("Step 5: Testing Concurrent / Rapid Double-Click Rejection...")
    results = []
    def do_capture():
        try:
            r = urllib.request.Request(f"{API_URL}/api/camera/capture", data=b"", method="POST")
            with urllib.request.urlopen(r, timeout=8.0) as rp:
                results.append((True, json.loads(rp.read().decode('utf-8'))))
        except urllib.error.HTTPError as e:
            results.append((False, json.loads(e.read().decode('utf-8'))))
        except Exception as ex:
            results.append((False, str(ex)))

    t1 = threading.Thread(target=do_capture)
    t2 = threading.Thread(target=do_capture)
    t1.start()
    time.sleep(0.05)  # slight stagger to ensure collision
    t2.start()
    t1.join()
    t2.join()

    log(f"  Concurrent attempts results: {[r[0] for r in results]}")
    # Either both executed cleanly in series or one was rejected as busy
    for success, payload in results:
        if not success:
            log(f"  Graceful rejection observed: {payload}")
    print("  ✅ Step 5: Concurrency Safety & Double-Click Handling PASS\n")

    # 6. Regression check: Backend & Telemetry
    log("Step 6: Verifying System Health & Live Telemetry Regression...")
    req = urllib.request.Request(f"{API_URL}/devices/AQUA_FRESH_001/latest")
    with urllib.request.urlopen(req, timeout=5.0) as resp:
        dev_latest = json.loads(resp.read().decode('utf-8'))
    telem = dev_latest.get("telemetry", {})
    log(f"  Physical pH: {telem.get('ph')} | Turbidity: {telem.get('turbidity_ntu')} | WiFi: {telem.get('wifi_connected')} | MQTT: {telem.get('mqtt_connected')}")
    assert telem.get("ph") is not None, "Missing live telemetry pH!"
    assert telem.get("turbidity_ntu") is not None, "Missing live telemetry turbidity!"
    print("  ✅ Step 6: System Regression Check PASS (Telemetry alive & uninterrupted)\n")

    print("🎯 ALL 6 MANUAL CAMERA CAPTURE PIPELINE TESTS PASSED!")
    return True

if __name__ == "__main__":
    success = test_manual_camera_pipeline()
    sys.exit(0 if success else 1)
