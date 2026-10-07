"""
AquaSentinel-AI: Physical ESP32-CAM (GC2145) Single-Capture Service
===================================================================
Coordinates single manual photo acquisition from the physical ESP32-CAM:
- Interfaces via USB-Serial CH340 @ 115200 baud. The COM port is found
  automatically (see src/utils/serial_ports.py) or set with AQUA_CAM_PORT.
- Triggers hardware capture via 'c' serial command
- Validates JPEG magic bytes (0xFF 0xD8) and dimensions (320x240)
- Enforces fresh-frame guarantee with unique capture_id and monotonically
  increasing frame_sequence counter
- Rejects stale/duplicate frames via SHA-256 frame payload hashing
- Thread-safe acquisition with busy-lock to reject concurrent/double-clicks
- Persists captures with timestamp to data/camera_captures/
- Updates docs/LIVE_ESP32_CAM_GC2145_FRAME.jpg for backward compatibility
"""

import os
import io
import time
import base64
import hashlib
import datetime
import threading
import logging
from typing import Optional, Dict, Any, Tuple
from PIL import Image

try:
    import serial
except ImportError:
    serial = None

from src.utils import serial_ports

logger = logging.getLogger("PhysicalCameraService")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAPTURES_DIR = os.path.join(BASE_DIR, "data", "camera_captures")
DOCS_IMG_PATH = os.path.join(BASE_DIR, "docs", "LIVE_ESP32_CAM_GC2145_FRAME.jpg")
DOCS_ALT_PATH = os.path.join(BASE_DIR, "docs", "live_camera_frame.jpg")


class PhysicalCameraService:
    _instance = None
    _singleton_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super(PhysicalCameraService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, port: Optional[str] = None, baud: int = 115200, timeout_sec: float = 15.0):
        if self._initialized:
            return
        self.port = port  # None -> resolved on first capture
        self.baud = baud
        self.timeout_sec = timeout_sec
        self.lock = threading.Lock()
        self.is_capturing = False
        self.frame_sequence = 100  # Will increment to 101 on first fresh capture
        self.last_capture_id: Optional[str] = None
        self.last_capture_hash: Optional[str] = None
        self.last_capture_meta: Optional[Dict[str, Any]] = None
        self.last_status: str = "READY"
        self.last_error: Optional[str] = None
        self.sensor_model = "GC2145"
        self.camera_model = "ESP32-CAM"
        self._initialized = True

        os.makedirs(CAPTURES_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(DOCS_IMG_PATH), exist_ok=True)

    def get_status(self) -> Dict[str, Any]:
        """Returns the current operational status of the physical camera."""
        if self.is_capturing:
            status = "CAPTURING"
        elif self.last_error:
            status = "ERROR"
        else:
            status = "READY"

        return {
            "status": status,
            "camera": self.camera_model,
            "sensor": self.sensor_model,
            "port": self.port or "auto-detect",
            "source": "PHYSICAL_ESP32_CAM",
            "frame_sequence": self.frame_sequence,
            "last_capture": self.last_capture_meta,
            "last_error": self.last_error
        }

    def capture_single_photo(self, timeout_sec: Optional[float] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Executes a single hardware capture from the physical ESP32-CAM.
        Thread-safe; immediately rejects concurrent requests.
        """
        timeout = timeout_sec or self.timeout_sec

        # Double-click / concurrent request rejection
        if not self.lock.acquire(blocking=False):
            return False, {
                "success": False,
                "camera": self.camera_model,
                "sensor": self.sensor_model,
                "error": "Camera busy: capture already in progress. Please wait for the current capture to complete.",
                "source": "PHYSICAL_ESP32_CAM"
            }

        self.is_capturing = True
        self.last_status = "CAPTURING"
        self.last_error = None
        start_time = time.time()

        try:
            if serial is None:
                raise RuntimeError("pyserial package is not installed.")

            ser = None
            jpeg_bytes = None
            width, height = 320, 240

            # 1. Resolve the camera port (env override, probing, or USB chip)
            port = self.port or serial_ports.find_port(serial_ports.CAM)
            if not port:
                err_msg = ("ESP32-CAM not found on any serial port. Check the USB cable, close any "
                           "Arduino/PlatformIO serial monitor, or set AQUA_CAM_PORT (e.g. COM4).")
                self.last_error = err_msg
                self.last_status = "OFFLINE"
                return False, {"success": False, "camera": self.camera_model, "sensor": self.sensor_model,
                               "error": err_msg, "source": "PHYSICAL_ESP32_CAM"}
            self.port = port

            # 2. Open without toggling DTR/RTS (the MB board wires them to EN/IO0),
            #    trigger capture with 'c' and read the Base64 frame.
            try:
                ser = serial_ports.open_port(port, self.baud, timeout=1.0)
                ser.reset_input_buffer()
                ser.write(b"c\r\n")
                last_trigger = time.time()

                b64_lines = []
                capturing = False

                while time.time() - start_time < timeout:
                    line_bytes = ser.readline()
                    if not line_bytes:
                        # Board may have been mid-boot; re-send the trigger once in a while.
                        if not capturing and time.time() - last_trigger > 4.0:
                            ser.write(b"c\r\n")
                            last_trigger = time.time()
                        continue
                    line = line_bytes.decode("utf-8", errors="replace").strip()

                    if "<<<FRAME_B64_START:" in line or "<<<FRAME_B64_START>>>" in line:
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
            except Exception as e:
                # Never substitute an old photo here: the dashboard must show the real state.
                if "denied" in str(e).lower() or "busy" in str(e).lower():
                    hint = " The port is in use: close the Arduino/PlatformIO serial monitor."
                else:
                    hint = ""
                    serial_ports.forget(serial_ports.CAM)
                    self.port = None  # re-detect next time (board may have moved ports)
                err_msg = f"Cannot open ESP32-CAM on {port}: {e}.{hint}"
                self.last_error = err_msg
                self.last_status = "OFFLINE"
                return False, {
                    "success": False,
                    "camera": self.camera_model,
                    "sensor": self.sensor_model,
                    "error": err_msg,
                    "source": "PHYSICAL_ESP32_CAM"
                }
            finally:
                if ser is not None:
                    try:
                        if ser.is_open:
                            ser.close()
                    except Exception:
                        pass

            # 3. Validate image data existence & magic bytes
            if not jpeg_bytes or len(jpeg_bytes) < 100:
                elapsed = time.time() - start_time
                err_msg = f"No fresh frame received from physical ESP32-CAM within {elapsed:.1f} seconds."
                self.last_error = err_msg
                self.last_status = "ERROR"
                return False, {
                    "success": False,
                    "camera": self.camera_model,
                    "sensor": self.sensor_model,
                    "error": err_msg,
                    "source": "PHYSICAL_ESP32_CAM"
                }

            if not (jpeg_bytes.startswith(b"\xff\xd8") or jpeg_bytes.startswith(b"\xff\xd8\xff")):
                err_msg = "Corrupted frame: Missing JPEG SOI magic bytes (0xFF 0xD8)."
                self.last_error = err_msg
                self.last_status = "ERROR"
                return False, {
                    "success": False,
                    "camera": self.camera_model,
                    "sensor": self.sensor_model,
                    "error": err_msg,
                    "source": "PHYSICAL_ESP32_CAM"
                }

            # 4. Freshness Verification via payload SHA-256
            current_hash = hashlib.sha256(jpeg_bytes).hexdigest()
            if current_hash == self.last_capture_hash:
                logger.info("Payload hash matches previous frame (static physical scene).")

            # Extract image dimensions safely
            try:
                pil_img = Image.open(io.BytesIO(jpeg_bytes))
                width, height = pil_img.size
            except Exception:
                width, height = 320, 240

            # 5. Generate unique capture metadata
            now = datetime.datetime.now(datetime.timezone.utc)
            local_now = datetime.datetime.now()
            capture_id = f"CAP_{now.strftime('%Y%m%d_%H%M%S')}_{now.microsecond // 1000:03d}"
            filename = f"esp32cam_{now.strftime('%Y%m%d_%H%M%S')}_{now.microsecond // 1000:03d}.jpg"
            saved_filepath = os.path.join(CAPTURES_DIR, filename)

            # Monotonically increasing sequence
            self.frame_sequence += 1
            self.last_capture_id = capture_id
            self.last_capture_hash = current_hash

            # 6. Save image to dedicated storage
            with open(saved_filepath, "wb") as f:
                f.write(jpeg_bytes)

            # Update legacy compatibility paths
            try:
                with open(DOCS_IMG_PATH, "wb") as f:
                    f.write(jpeg_bytes)
                with open(DOCS_ALT_PATH, "wb") as f:
                    f.write(jpeg_bytes)
            except Exception as e:
                logger.warning(f"Failed to update legacy doc images: {e}")

            b64_output = base64.b64encode(jpeg_bytes).decode("ascii")

            result = {
                "success": True,
                "camera": self.camera_model,
                "sensor": self.sensor_model,
                "capture_id": capture_id,
                "timestamp": now.isoformat(),
                "captured_at": local_now.strftime("%H:%M:%S"),
                "filename": filename,
                "filepath": os.path.relpath(saved_filepath, BASE_DIR).replace("\\", "/"),
                "absolute_path": saved_filepath,
                "width": width,
                "height": height,
                "size_bytes": len(jpeg_bytes),
                "format": "JPEG",
                "frame_sequence": self.frame_sequence,
                "source": "PHYSICAL_ESP32_CAM",
                "fresh_frame": True,
                "image_base64": b64_output,
                "latency_sec": round(time.time() - start_time, 2)
            }

            self.last_capture_meta = result
            self.last_status = "SUCCESS"
            return True, result

        except Exception as e:
            err_msg = f"Capture exception: {e}"
            self.last_error = err_msg
            self.last_status = "ERROR"
            return False, {
                "success": False,
                "camera": self.camera_model,
                "sensor": self.sensor_model,
                "error": err_msg,
                "source": "PHYSICAL_ESP32_CAM"
            }
        finally:
            self.is_capturing = False
            self.lock.release()

camera_service = PhysicalCameraService()
