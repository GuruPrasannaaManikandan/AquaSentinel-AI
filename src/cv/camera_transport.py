import io
import base64
import json
import time
import logging
import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple, List
from PIL import Image

from src.cv.camera_driver import CameraFrame, BaseCameraDriver
from src.iot.mqtt_client import MQTTClient
from src.cv.temporal_validator import TemporalValidator, TemporalValidationResult

MAX_PAYLOAD_SIZE_BYTES = 500 * 1024  # 500 KB payload safety cap


@dataclass
class CameraMessageContract:
    """
    Formal transport contract for ESP32-CAM MQTT payloads (Schema Version 1.1).
    Encapsulates raw image bytes, spatial dimensions, capture timestamps, SNTP sync status,
    clock source, and hardware metadata.
    """
    device_id: str
    frame_id: str
    timestamp: str                               # Wall-clock ISO-8601 string
    width: int
    height: int
    channels: int
    format: str                                  # "JPEG", "PNG", "RGB"
    image_bytes: bytes
    status: str = "OK"                           # "OK", "CORRUPTED", "EXPOSURE_FAULT", "CAMERA_OFFLINE", "OVERSIZED_PAYLOAD"
    quality_valid: bool = True
    schema_version: str = "1.1"
    time_sync_status: str = "SYNCED"             # "SYNCED", "UNSYNCED" (Default SYNCED for backward compatibility)
    clock_source: str = "NTP"                    # "NTP", "UNSYNCED_BOOT_TICK", "RTC", "UNKNOWN"
    capture_timestamp: Optional[str] = None      # Explicit frame capture timestamp
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.capture_timestamp:
            self.capture_timestamp = self.timestamp

    def to_mqtt_payload(self) -> Dict[str, Any]:
        """Serializes contract into a JSON-compatible dictionary with Base64 JPEG encoding."""
        b64_str = base64.b64encode(self.image_bytes).decode("utf-8") if self.image_bytes else ""
        return {
            "schema_version": self.schema_version,
            "device_id": self.device_id,
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "capture_timestamp": self.capture_timestamp or self.timestamp,
            "time_sync_status": self.time_sync_status,
            "clock_source": self.clock_source,
            "width": self.width,
            "height": self.height,
            "channels": self.channels,
            "format": self.format,
            "status": self.status,
            "quality_valid": self.quality_valid,
            "image_b64": b64_str,
            "metadata": self.metadata
        }

    @classmethod
    def from_mqtt_payload(cls, payload: Dict[str, Any]) -> Tuple[Optional["CameraMessageContract"], bool, str]:
        """
        Deserializes and validates an incoming MQTT JSON payload into a CameraMessageContract.
        Returns (contract, is_valid, error_code).
        """
        if not isinstance(payload, dict):
            return None, False, "INVALID_PAYLOAD_TYPE"

        # Check required fields
        required_fields = ["device_id", "frame_id", "timestamp", "image_b64"]
        for f in required_fields:
            if f not in payload or payload[f] is None:
                return None, False, f"MISSING_{f.upper()}"

        device_id = str(payload["device_id"])
        frame_id = str(payload["frame_id"])
        timestamp = str(payload["timestamp"])

        # Timestamp format validation
        try:
            clean_ts = timestamp.rstrip("Z")
            datetime.datetime.fromisoformat(clean_ts)
        except (ValueError, TypeError):
            return None, False, "INVALID_TIMESTAMP"

        b64_str = payload["image_b64"]
        if not b64_str or len(b64_str) == 0:
            return None, False, "EMPTY_PAYLOAD"

        # Size threshold validation before decoding
        if len(b64_str) > (MAX_PAYLOAD_SIZE_BYTES * 4 // 3 + 1024):
            return None, False, "OVERSIZED_PAYLOAD"

        # Decode Base64 JPEG bytes
        try:
            img_bytes = base64.b64decode(b64_str)
        except Exception:
            return None, False, "DECODE_FAILURE"

        if len(img_bytes) == 0:
            return None, False, "EMPTY_PAYLOAD"

        if len(img_bytes) > MAX_PAYLOAD_SIZE_BYTES:
            return None, False, "OVERSIZED_PAYLOAD"

        # Header check for JPEG magic bytes (0xFF 0xD8)
        if payload.get("format", "JPEG").upper() == "JPEG":
            if not (img_bytes.startswith(b"\xff\xd8") or img_bytes.startswith(b"\xff\xd8\xff")):
                return None, False, "CORRUPTED"

        schema_ver = str(payload.get("schema_version", "1.0"))
        # Default SYNCED for backward compatibility with schema 1.0 payloads
        default_sync = "SYNCED" if schema_ver == "1.0" or "time_sync_status" not in payload else "UNSYNCED"
        time_sync_status = str(payload.get("time_sync_status", default_sync))
        clock_source = str(payload.get("clock_source", "NTP" if time_sync_status == "SYNCED" else "UNKNOWN"))
        capture_timestamp = str(payload.get("capture_timestamp", timestamp))

        width = int(payload.get("width", 224))
        height = int(payload.get("height", 224))
        channels = int(payload.get("channels", 3))
        fmt = str(payload.get("format", "JPEG"))
        status = str(payload.get("status", "OK"))
        quality_valid = bool(payload.get("quality_valid", True))
        metadata = payload.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        contract = cls(
            device_id=device_id,
            frame_id=frame_id,
            timestamp=timestamp,
            width=width,
            height=height,
            channels=channels,
            format=fmt,
            image_bytes=img_bytes,
            status=status,
            quality_valid=quality_valid,
            schema_version=schema_ver,
            time_sync_status=time_sync_status,
            clock_source=clock_source,
            capture_timestamp=capture_timestamp,
            metadata=metadata
        )

        return contract, True, "OK"


class CameraTransportReceiver(BaseCameraDriver):
    """
    Gateway-Side Camera Transport Receiver (V4.8.3).
    Subscribes to MQTT camera topics (`aquatic/+/camera/raw`), deserializes incoming payloads,
    attaches Gateway receive timestamps, runs TemporalValidator, manages frame deduplication,
    and generates standard `CameraFrame` instances.
    """
    def __init__(
        self,
        name: str = "CAM_TRANSPORT_RECEIVER",
        mqtt_client: Optional[MQTTClient] = None,
        topic_pattern: str = "aquatic/+/camera/raw",
        resolution: Tuple[int, int] = (224, 224),
        config: Optional[dict] = None,
        temporal_validator: Optional[TemporalValidator] = None
    ):
        super().__init__(name=name, resolution=resolution, config=config)
        self.topic_pattern = topic_pattern
        self.client = mqtt_client
        self.temporal_validator = temporal_validator or TemporalValidator()
        self.received_frames_history: List[CameraFrame] = []
        self.seen_frame_ids: set = set()
        self.last_timestamp: Optional[datetime.datetime] = None
        self.latest_frame: Optional[CameraFrame] = None
        self.camera_online = True
        self.dropped_duplicate_count = 0
        self.dropped_stale_count = 0
        self.fault_count = 0

    def init(self) -> bool:
        """Initializes receiver and registers MQTT subscriber callback."""
        self.status = "ONLINE"
        if self.client:
            if not self.client.connected:
                self.client.connect()
            self.client.subscribe(self.topic_pattern)
            # Store existing callback if present to chain calls
            existing_cb = self.client.message_callback

            def _combined_callback(topic, payload):
                if existing_cb:
                    try:
                        existing_cb(topic, payload)
                    except Exception as e:
                        logging.error(f"Error in existing MQTT callback: {e}")
                self.on_mqtt_message_received(topic, payload)

            self.client.set_on_message(_combined_callback)
        return True

    def on_mqtt_message_received(self, topic: str, payload: Any):
        """Processes incoming MQTT payload from ESP32-CAM."""
        if "/camera/" not in topic:
            return

        if not self.camera_online:
            return

        start_monotonic = time.perf_counter()
        gw_receive_iso = datetime.datetime.now().isoformat()

        # Attempt to parse contract
        contract, is_valid, err_code = CameraMessageContract.from_mqtt_payload(payload if isinstance(payload, dict) else {})

        if not is_valid or contract is None:
            self.fault_count += 1
            frame_id = payload.get("frame_id", f"fault_{self.frame_count + 1}") if isinstance(payload, dict) else f"fault_{self.frame_count + 1}"
            ts = payload.get("timestamp", gw_receive_iso) if isinstance(payload, dict) else gw_receive_iso
            
            fault_frame = CameraFrame(
                frame_id=frame_id,
                timestamp=ts,
                width=self.resolution[0],
                height=self.resolution[1],
                channels=3,
                format="JPEG",
                image_bytes=b"",
                quality_valid=False,
                status=err_code,
                metadata={
                    "error": f"Camera payload fault: {err_code}",
                    "raw_topic": topic,
                    "capture_timestamp": ts,
                    "gateway_receive_timestamp": gw_receive_iso,
                    "time_sync_status": payload.get("time_sync_status", "UNSYNCED") if isinstance(payload, dict) else "UNSYNCED",
                    "clock_source": payload.get("clock_source", "UNKNOWN") if isinstance(payload, dict) else "UNKNOWN",
                    "temporal_valid": False,
                    "temporal_status": err_code,
                    "reason_code": f"VISUAL_{err_code}"
                }
            )
            self.latest_frame = fault_frame
            self.received_frames_history.append(fault_frame)
            return

        # Check duplicate frame_id
        if contract.frame_id in self.seen_frame_ids:
            self.dropped_duplicate_count += 1
            logging.warning(f"Duplicate camera frame_id received and dropped: {contract.frame_id}")
            return

        # Check timestamp temporal order (safety check: drop stale frames)
        try:
            curr_dt = self.temporal_validator.parse_iso_timestamp(contract.timestamp)
            if curr_dt and self.last_timestamp and curr_dt < self.last_timestamp:
                self.dropped_stale_count += 1
                logging.warning(f"Stale camera timestamp received and dropped: {contract.timestamp} < {self.last_timestamp}")
                return
            elif curr_dt:
                self.last_timestamp = curr_dt
        except Exception:
            pass

        # Run Temporal Validation
        temporal_res = self.temporal_validator.validate_camera_frame_temporal(
            capture_ts_str=contract.capture_timestamp or contract.timestamp,
            time_sync_status=contract.time_sync_status,
            clock_source=contract.clock_source,
            gateway_receive_ts_str=gw_receive_iso,
            start_monotonic=start_monotonic
        )

        self.seen_frame_ids.add(contract.frame_id)
        self.frame_count += 1

        # Determine frame status and validity incorporating temporal validation
        frame_status = contract.status
        quality_valid = contract.quality_valid and (contract.status == "OK") and temporal_res.temporal_valid

        if not temporal_res.temporal_valid:
            quality_valid = False
            frame_status = temporal_res.reason_code

        # Construct CameraFrame object preserving multi-tier temporal metadata
        camera_frame = CameraFrame(
            frame_id=contract.frame_id,
            timestamp=contract.timestamp,
            width=contract.width,
            height=contract.height,
            channels=contract.channels,
            format=contract.format,
            image_bytes=contract.image_bytes,
            quality_valid=quality_valid,
            status=frame_status,
            metadata={
                "driver": self.name,
                "device_id": contract.device_id,
                "schema_version": contract.schema_version,
                "capture_timestamp": contract.capture_timestamp or contract.timestamp,
                "gateway_receive_timestamp": gw_receive_iso,
                "time_sync_status": contract.time_sync_status,
                "clock_source": contract.clock_source,
                "temporal_valid": temporal_res.temporal_valid,
                "temporal_status": temporal_res.temporal_status,
                "reason_code": temporal_res.reason_code,
                "frame_age_ms": temporal_res.frame_age_ms,
                "monotonic_latency_ms": temporal_res.monotonic_latency_ms,
                **contract.metadata
            }
        )

        self.latest_frame = camera_frame
        self.received_frames_history.append(camera_frame)

    def set_camera_offline(self):
        """Simulates camera hardware disconnection."""
        self.camera_online = False
        self.status = "OFFLINE"
        now_iso = datetime.datetime.now().isoformat()
        self.latest_frame = CameraFrame(
            frame_id=f"frame_offline_{self.frame_count}",
            timestamp=now_iso,
            width=self.resolution[0],
            height=self.resolution[1],
            channels=3,
            format="JPEG",
            image_bytes=b"",
            quality_valid=False,
            status="CAMERA_OFFLINE",
            metadata={
                "driver": self.name,
                "error": "Camera hardware disconnected",
                "capture_timestamp": now_iso,
                "gateway_receive_timestamp": now_iso,
                "time_sync_status": "UNSYNCED",
                "clock_source": "UNKNOWN",
                "temporal_valid": False,
                "temporal_status": "CAMERA_OFFLINE",
                "reason_code": "VISUAL_CAMERA_FAULT"
            }
        )

    def capture_frame(self) -> CameraFrame:
        """Returns the latest acquired CameraFrame or an offline fault frame."""
        now_iso = datetime.datetime.now().isoformat()
        if not self.camera_online or self.status == "OFFLINE":
            return CameraFrame(
                frame_id=f"frame_offline_{self.frame_count}",
                timestamp=now_iso,
                width=self.resolution[0],
                height=self.resolution[1],
                channels=3,
                format="JPEG",
                image_bytes=b"",
                quality_valid=False,
                status="CAMERA_OFFLINE",
                metadata={
                    "driver": self.name,
                    "error": "Camera hardware offline",
                    "capture_timestamp": now_iso,
                    "gateway_receive_timestamp": now_iso,
                    "time_sync_status": "UNSYNCED",
                    "clock_source": "UNKNOWN",
                    "temporal_valid": False,
                    "temporal_status": "CAMERA_OFFLINE",
                    "reason_code": "VISUAL_CAMERA_FAULT"
                }
            )

        if self.latest_frame is not None:
            return self.latest_frame

        return CameraFrame(
            frame_id=f"frame_none_{self.frame_count}",
            timestamp=now_iso,
            width=self.resolution[0],
            height=self.resolution[1],
            channels=3,
            format="JPEG",
            image_bytes=b"",
            quality_valid=False,
            status="CAMERA_OFFLINE",
            metadata={
                "driver": self.name,
                "error": "No camera frame received yet",
                "capture_timestamp": now_iso,
                "gateway_receive_timestamp": now_iso,
                "time_sync_status": "UNSYNCED",
                "clock_source": "UNKNOWN",
                "temporal_valid": False,
                "temporal_status": "CAMERA_OFFLINE",
                "reason_code": "VISUAL_CAMERA_FAULT"
            }
        )
