"""
verify_camera.py
Companion Verification & Image Acquisition Tool for Phase B–I
Connects to COM4, records ESP32-CAM serial logs, extracts Base64 JPEG frames,
and performs forensic quality validation.
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
TIMEOUT = 0.5
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "reports", "camera_verification")
OUTPUT_DIR = os.path.abspath(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)
IMAGE_OUT_PATH = os.path.join(OUTPUT_DIR, "verified_frame.jpg")
LOG_OUT_PATH = os.path.join(OUTPUT_DIR, "camera_verification_log.txt")


def analyze_image(jpeg_bytes: bytes) -> dict:
    """Performs image quality and corruption checks on raw JPEG bytes."""
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

    # JPEG SOI (0xFF, 0xD8) and EOI (0xFF, 0xD9)
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


def run_verification(listen_seconds: int = 60):
    print("==================================================================", flush=True)
    print("   AquaSentinel-AI: ESP32-CAM Hardware Verification Tool", flush=True)
    print(f"   Serial Port: {PORT} @ {BAUD} baud", flush=True)
    print(f"   Output Directory: {OUTPUT_DIR}", flush=True)
    print(f"   Listening Duration: {listen_seconds}s", flush=True)
    print("==================================================================", flush=True)

    s = None
    print(f"[STATUS] Waiting for {PORT} to become available...", flush=True)
    wait_start = time.time()
    while time.time() - wait_start < 30:
        try:
            s = serial.Serial(PORT, BAUD, timeout=TIMEOUT)
            break
        except Exception:
            time.sleep(0.5)

    if not s or not s.is_open:
        print(f"[ERROR] Could not open {PORT} after 30s.", flush=True)
        return False

    print("[STATUS] Serial port opened. Waiting for ESP32-CAM output...", flush=True)
    print("------------------------------------------------------------------", flush=True)

    # Send trigger newline + 'i' (initialize) command in case board is already running
    try:
        s.write(b"\r\n\r\n")
        time.sleep(0.1)
    except Exception:
        pass

    log_lines = []
    b64_buffer = []
    capturing_b64 = False
    captured_jpeg_bytes = None
    start_time = time.time()

    while time.time() - start_time < listen_seconds:
        try:
            line_bytes = s.readline()
        except Exception as e:
            time.sleep(0.2)
            continue

        if not line_bytes:
            continue

        line_str = line_bytes.decode("utf-8", errors="replace").strip()
        if not line_str:
            continue

        log_lines.append(line_str)

        # Detect Base64 image payload start
        if "<<<FRAME_B64_START:" in line_str:
            capturing_b64 = True
            b64_buffer = []
            print(f"[SERIAL] {line_str} -> Capturing incoming frame stream...", flush=True)
            continue

        if "<<<FRAME_B64_END>>>" in line_str:
            capturing_b64 = False
            full_b64 = "".join(b64_buffer)
            print(f"[SERIAL] Received complete Base64 frame payload ({len(full_b64)} chars).", flush=True)
            try:
                captured_jpeg_bytes = base64.b64decode(full_b64)
                print(f"[SUCCESS] Decoded {len(captured_jpeg_bytes)} binary JPEG bytes.", flush=True)
            except Exception as ex:
                print(f"[ERROR] Base64 decode failure: {ex}", flush=True)
            continue

        if capturing_b64:
            b64_buffer.append(line_str)
        else:
            print(f"[ESP32] {line_str}", flush=True)

    try:
        s.close()
    except Exception:
        pass

    print("------------------------------------------------------------------", flush=True)
    print(f"[STATUS] Serial session closed. Total log lines captured: {len(log_lines)}", flush=True)

    # Write full log file
    with open(LOG_OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    print(f"[LOG] Log saved to: {LOG_OUT_PATH}", flush=True)

    # Analyze captured frame if available
    if captured_jpeg_bytes:
        with open(IMAGE_OUT_PATH, "wb") as f:
            f.write(captured_jpeg_bytes)
        print(f"[IMAGE] Frame written to: {IMAGE_OUT_PATH}", flush=True)

        print("[ANALYSIS] Running image quality and integrity analysis...", flush=True)
        analysis = analyze_image(captured_jpeg_bytes)
        print("------------------------------------------------------------------", flush=True)
        print(f"  Valid JPEG Format     : {'PASS' if analysis['valid_jpeg'] else 'FAIL'}")
        print(f"  Dimensions            : {analysis['width']} x {analysis['height']}")
        print(f"  Channels              : {analysis['channels']}")
        print(f"  Pixel Range           : [{analysis['min_pixel']}, {analysis['max_pixel']}]")
        print(f"  Mean Intensity        : {analysis['mean_pixel']:.2f} / 255.0")
        print(f"  Pixel Std Dev         : {analysis['std_pixel']:.2f}")
        print(f"  Not All-Black Check   : {'PASS' if not analysis['is_all_black'] else 'FAIL'}")
        print(f"  Not All-White Check   : {'PASS' if not analysis['is_all_white'] else 'FAIL'}")
        print(f"  Optical Status        : {analysis['status']}")
        print("------------------------------------------------------------------", flush=True)

        if analysis["status"] == "VALID_OPTICAL_IMAGE":
            print(">>> IMAGE VERIFICATION: PASS (Optical frame validated) <<<", flush=True)
            return True
        else:
            print(f">>> IMAGE VERIFICATION: FAIL ({analysis['status']}) <<<", flush=True)
            return False
    else:
        print("[WARNING] No Base64 image payload was intercepted during the session.", flush=True)
        return False


if __name__ == "__main__":
    run_verification(listen_seconds=45)
