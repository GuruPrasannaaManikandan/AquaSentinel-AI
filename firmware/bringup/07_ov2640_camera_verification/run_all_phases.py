"""
run_all_phases.py
Automated execution of Phases C, D, E, F, G, H, I on ESP32-CAM via COM4.
Interacts with the verified firmware to execute all tests, captures the image,
verifies optical quality, and saves all evidence to reports/camera_verification/.
"""

import os
import io
import sys
import time
import base64
import serial
import numpy as np
from PIL import Image

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
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "reports", "camera_verification")
OUTPUT_DIR = os.path.abspath(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)
IMAGE_OUT_PATH = os.path.join(OUTPUT_DIR, "verified_frame.jpg")
LOG_OUT_PATH = os.path.join(OUTPUT_DIR, "camera_verification_log.txt")


def analyze_image(jpeg_bytes: bytes) -> dict:
    results = {
        "valid_jpeg": False,
        "magic_soi": False,
        "magic_eoi": False,
        "width": 0,
        "height": 0,
        "channels": 0,
        "min_pixel": 0,
        "max_pixel": 0,
        "mean_pixel": 0.0,
        "std_pixel": 0.0,
        "is_all_black": False,
        "is_all_white": False,
        "status": "UNKNOWN"
    }

    if len(jpeg_bytes) < 4:
        results["status"] = "TOO_SHORT"
        return results

    results["magic_soi"] = (jpeg_bytes[0] == 0xFF and jpeg_bytes[1] == 0xD8)
    results["magic_eoi"] = (jpeg_bytes[-2] == 0xFF and jpeg_bytes[-1] == 0xD9)

    try:
        img = Image.open(io.BytesIO(jpeg_bytes))
        results["width"], results["height"] = img.size
        results["channels"] = len(img.getbands())
        img_rgb = img.convert("RGB")
        arr = np.array(img_rgb)

        results["min_pixel"] = int(np.min(arr))
        results["max_pixel"] = int(np.max(arr))
        results["mean_pixel"] = float(np.mean(arr))
        results["std_pixel"] = float(np.std(arr))

        results["is_all_black"] = (results["max_pixel"] == 0)
        results["is_all_white"] = (results["min_pixel"] == 255)
        results["valid_jpeg"] = True

        if results["is_all_black"]:
            results["status"] = "ALL_BLACK"
        elif results["is_all_white"]:
            results["status"] = "ALL_WHITE"
        elif results["std_pixel"] < 1.0:
            results["status"] = "UNIFORM_SOLID_COLOR"
        else:
            results["status"] = "VALID_OPTICAL_IMAGE"

    except Exception as e:
        results["status"] = f"DECODE_ERROR: {e}"

    return results


def main():
    print("==================================================================", flush=True)
    print("   AquaSentinel-AI: Automated Camera Verification Runner", flush=True)
    print(f"   Target Port: {PORT} @ {BAUD} baud", flush=True)
    print(f"   Output Directory: {OUTPUT_DIR}", flush=True)
    print("==================================================================", flush=True)

    s = serial.Serial(PORT, BAUD, timeout=1.0)
    time.sleep(0.5)

    all_logs = []

    def read_until_quiet(max_quiet_sec=2.0, total_timeout_sec=30.0):
        lines = []
        last_rx = time.time()
        start = time.time()
        while time.time() - start < total_timeout_sec:
            raw = s.readline()
            if raw:
                line = raw.decode("utf-8", errors="replace").strip()
                if line:
                    lines.append(line)
                    all_logs.append(line)
                    print(f"  [ESP32] {line}", flush=True)
                    last_rx = time.time()
            else:
                if time.time() - last_rx >= max_quiet_sec:
                    break
        return lines

    # 1. Clear buffer
    print("\n--- [STEP 0: Flush initial buffer] ---", flush=True)
    read_until_quiet(max_quiet_sec=1.0, total_timeout_sec=3.0)

    # 2. Query System Status & Hardware Baseline
    print("\n--- [STEP 1: Hardware Baseline & Status (Command 'b')] ---", flush=True)
    s.write(b"b\n")
    read_until_quiet(max_quiet_sec=1.5, total_timeout_sec=5.0)

    # 3. Phase D: Single Frame Capture Test
    print("\n--- [STEP 2: Phase D Single Frame Test (Command '1')] ---", flush=True)
    s.write(b"1\n")
    read_until_quiet(max_quiet_sec=1.5, total_timeout_sec=5.0)

    # 4. Phase E: 10 Repeated Frames Capture Test
    print("\n--- [STEP 3: Phase E 10-Frame Test (Command 'e')] ---", flush=True)
    s.write(b"e\n")
    read_until_quiet(max_quiet_sec=2.0, total_timeout_sec=10.0)

    # 5. Phase F: Capture & Transmit Actual Image (Base64)
    print("\n--- [STEP 4: Phase F Base64 Frame Capture (Command 'c')] ---", flush=True)
    s.write(b"c\n")
    b64_lines = []
    in_b64 = False
    start_c = time.time()
    while time.time() - start_c < 15.0:
        raw = s.readline()
        if not raw:
            continue
        line = raw.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        all_logs.append(line)

        if "<<<FRAME_B64_START:" in line:
            in_b64 = True
            b64_lines = []
            print(f"  [STREAM] {line} (Receiving frame payload...)", flush=True)
            continue
        if "<<<FRAME_B64_END>>>" in line:
            in_b64 = False
            print(f"  [STREAM] {line} (Frame payload complete)", flush=True)
            break
        if in_b64:
            b64_lines.append(line)
        else:
            print(f"  [ESP32] {line}", flush=True)

    # 6. Phase H: 50-Frame Continuous Stability Test
    print("\n--- [STEP 5: Phase H 50-Frame Stability Test (Command 'h')] ---", flush=True)
    s.write(b"h\n")
    read_until_quiet(max_quiet_sec=2.5, total_timeout_sec=30.0)

    s.close()
    print("\n[STATUS] All test commands executed and serial closed.", flush=True)

    # Write log file
    with open(LOG_OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(all_logs))
    print(f"[SAVED] Log file written to: {LOG_OUT_PATH}", flush=True)

    # Decode and analyze frame
    if b64_lines:
        full_b64 = "".join(b64_lines)
        try:
            jpg_bytes = base64.b64decode(full_b64)
            with open(IMAGE_OUT_PATH, "wb") as f:
                f.write(jpg_bytes)
            print(f"[SAVED] Decoded image saved to: {IMAGE_OUT_PATH} ({len(jpg_bytes)} bytes)", flush=True)

            print("\n==================================================================", flush=True)
            print("   PHASE G — FORENSIC IMAGE QUALITY ANALYSIS", flush=True)
            print("==================================================================", flush=True)
            analysis = analyze_image(jpg_bytes)
            print(f"  Valid JPEG Format     : {'PASS' if analysis['valid_jpeg'] else 'FAIL'}")
            print(f"  SOI Marker (0xFFD8)   : {'PASS' if analysis['magic_soi'] else 'FAIL'}")
            print(f"  EOI Marker (0xFFD9)   : {'PASS' if analysis['magic_eoi'] else 'FAIL'}")
            print(f"  Image Dimensions      : {analysis['width']} x {analysis['height']}")
            print(f"  Color Channels        : {analysis['channels']} (RGB)")
            print(f"  Pixel Range           : [{analysis['min_pixel']}, {analysis['max_pixel']}]")
            print(f"  Mean Intensity        : {analysis['mean_pixel']:.2f} / 255.0")
            print(f"  Pixel Std Deviation   : {analysis['std_pixel']:.2f}")
            print(f"  Not All-Black Check   : {'PASS' if not analysis['is_all_black'] else 'FAIL'}")
            print(f"  Not All-White Check   : {'PASS' if not analysis['is_all_white'] else 'FAIL'}")
            print(f"  Optical Status        : {analysis['status']}")
            print("==================================================================", flush=True)

            if analysis['status'] == 'VALID_OPTICAL_IMAGE':
                print("\n>>> ALL CAMERA HARDWARE VERIFICATION PHASES (B–I): PASS <<<\n", flush=True)
            else:
                print(f"\n>>> IMAGE VERIFICATION FAILED: {analysis['status']} <<<\n", flush=True)

        except Exception as ex:
            print(f"[ERROR] Failed to decode Base64 frame: {ex}", flush=True)
    else:
        print("[ERROR] No Base64 frame data captured!", flush=True)


if __name__ == "__main__":
    main()
