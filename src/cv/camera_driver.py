import os
import io
import time
import datetime
import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple
from PIL import Image, ImageDraw

@dataclass
class CameraFrame:
    """
    Structured container for acquired camera frames.
    Encapsulates raw image payload, spatial-temporal dimensions, validation status, and metadata.
    """
    frame_id: str
    timestamp: str  # ISO-8601 timestamp string
    width: int
    height: int
    channels: int
    format: str  # "RGB", "BGR", "JPEG", "PNG"
    image_bytes: bytes
    quality_valid: bool = True
    status: str = "OK"  # "OK", "CORRUPTED", "EXPOSURE_FAULT", "CAMERA_OFFLINE"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_pil_image(self) -> Optional[Image.Image]:
        """Converts raw image bytes or array representation to PIL Image object."""
        if not self.image_bytes or len(self.image_bytes) == 0:
            return None
        try:
            return Image.open(io.BytesIO(self.image_bytes))
        except Exception as e:
            logging.error(f"Failed to decode image bytes: {e}")
            return None

    def to_numpy_array(self) -> Optional[np.ndarray]:
        """Converts PIL Image to numpy array (H, W, C)."""
        pil_img = self.to_pil_image()
        if pil_img is None:
            return None
        return np.array(pil_img)


class BaseCameraDriver:
    """
    Abstract base driver interface for physical and virtual camera hardware.
    Ensures seamless compatibility between physical ESP32-CAM/RTSP drivers and simulation mocks.
    """
    def __init__(self, name: str = "CAM_01", resolution: Tuple[int, int] = (224, 224), config: Optional[dict] = None):
        self.name = name
        self.resolution = resolution  # (width, height)
        self.config = config or {}
        self.status = "UNINITIALIZED"
        self.frame_count = 0

    def init(self) -> bool:
        """Initializes camera hardware or virtual stream."""
        raise NotImplementedError("Subclasses must implement init()")

    def capture_frame(self) -> CameraFrame:
        """Captures and returns a single CameraFrame."""
        raise NotImplementedError("Subclasses must implement capture_frame()")

    def get_status(self) -> str:
        """Returns current operational status ('ONLINE', 'OFFLINE', 'FAULT')."""
        return self.status


class VirtualCameraDriver(BaseCameraDriver):
    """
    Virtual camera driver for software-first aquatic bloom visual detection.
    Generates synthetic or dataset-backed aquatic scene frames based on environmental scenario:
    - NORMAL: Clear blue-green water scene.
    - KNOWN_BLOOM_RISK / BLOOM: Dense green algal bloom discolored scene.
    - SENSOR_FAULT / CAMERA_FAULT: Corrupted/empty frame with quality_valid=False.
    """
    def __init__(self, name: str = "CAM_VIRTUAL_01", resolution: Tuple[int, int] = (224, 224), env=None, config: Optional[dict] = None):
        super().__init__(name=name, resolution=resolution, config=config)
        self.env = env  # Reference to VirtualEnvironment if available
        self.simulated_scenario = "NORMAL"
        self.fault_mode: Optional[str] = None

    def init(self) -> bool:
        """Initializes virtual camera stream."""
        self.status = "ONLINE"
        self.frame_count = 0
        return True

    def set_scenario(self, scenario: str):
        """Sets simulated visual scenario ('NORMAL', 'KNOWN_BLOOM_RISK', 'SENSOR_FAULT')."""
        self.simulated_scenario = scenario

    def set_fault(self, fault_type: Optional[str]):
        """Injects camera hardware fault ('CAMERA_OFFLINE', 'CORRUPTED_FRAME', None)."""
        self.fault_mode = fault_type
        if fault_type == "CAMERA_OFFLINE":
            self.status = "OFFLINE"
        elif fault_type is not None:
            self.status = "FAULT"
        else:
            self.status = "ONLINE"

    def _generate_synthetic_image(self, scenario: str, timestamp: datetime.datetime) -> Tuple[bytes, bool, str]:
        """
        Generates synthetic JPEG image bytes matching the aquatic scenario.
        Returns (image_bytes, quality_valid, status_code).
        """
        w, h = self.resolution

        # Check explicit fault modes
        if self.fault_mode == "CAMERA_OFFLINE":
            return b"", False, "CAMERA_OFFLINE"
        if self.fault_mode == "CORRUPTED_FRAME":
            return b"CORRUPTED_NON_IMAGE_DATA_BYTES", False, "CORRUPTED"

        # Check environmental scenario
        if scenario == "SENSOR_FAULT":
            return b"", False, "CAMERA_FAULT"

        img = Image.new("RGB", (w, h), color=(10, 80, 140)) # Default deep water blue
        draw = ImageDraw.Draw(img)

        if scenario in ["KNOWN_BLOOM_RISK", "BLOOM", "FRESHWATER_CONTEXT_RISK", "MARINE_BLOOM_RISK"]:
            # Draw dense green algal bloom patches across frame
            draw.rectangle([0, 0, w, h], fill=(30, 160, 50)) # Vibrant algae green
            # Add irregular surface bloom texture
            for _ in range(30):
                x0 = np.random.randint(0, w)
                y0 = np.random.randint(0, h)
                x1 = min(w, x0 + np.random.randint(20, 80))
                y1 = min(h, y0 + np.random.randint(20, 80))
                draw.ellipse([x0, y0, x1, y1], fill=(10, 200, 30))
        elif scenario in ["ENVIRONMENTAL_STRESS", "UNUSUAL_ENVIRONMENTAL_CONDITION"]:
            # Turbid brownish-sediment discoloration
            draw.rectangle([0, 0, w, h], fill=(150, 100, 30))
        else:
            # Clear aquatic water with subtle light ripples
            draw.rectangle([0, 0, w, h], fill=(20, 110, 170))
            for _ in range(15):
                x0 = np.random.randint(0, w)
                y0 = np.random.randint(0, h)
                draw.line([x0, y0, min(w, x0+40), y0], fill=(60, 150, 210), width=2)

        # Save to JPEG in-memory byte buffer
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue(), True, "OK"

    def capture_frame(self) -> CameraFrame:
        """
        Captures single CameraFrame with timestamp, validation, and availability metrics.
        """
        if self.status == "OFFLINE":
            return CameraFrame(
                frame_id=f"frame_{self.frame_count}",
                timestamp=datetime.datetime.now().isoformat(),
                width=self.resolution[0],
                height=self.resolution[1],
                channels=3,
                format="JPEG",
                image_bytes=b"",
                quality_valid=False,
                status="CAMERA_OFFLINE",
                metadata={"driver": self.name}
            )

        self.frame_count += 1
        now = datetime.datetime.now()
        
        # Determine scenario from VirtualEnvironment if attached
        scenario = self.simulated_scenario
        if self.env and hasattr(self.env, "scenario"):
            scenario = self.env.scenario

        img_bytes, is_valid, frame_status = self._generate_synthetic_image(scenario, now)

        return CameraFrame(
            frame_id=f"frame_{self.frame_count}",
            timestamp=now.isoformat(),
            width=self.resolution[0],
            height=self.resolution[1],
            channels=3,
            format="JPEG",
            image_bytes=img_bytes,
            quality_valid=is_valid,
            status=frame_status,
            metadata={
                "driver": self.name,
                "simulated_scenario": scenario,
                "frame_index": self.frame_count
            }
        )
