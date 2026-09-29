import time
import datetime
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple

# Default Engineering Thresholds (Based on 10-second sampling interval)
MAX_ALLOWED_FRAME_AGE_SEC = 30.0    # 3x sampling interval (30s max age threshold)
MAX_FUTURE_TOLERANCE_SEC = 5.0      # Clock skew tolerance window (5s max future bias)
MAX_SENSOR_VISUAL_DELTA_SEC = 15.0  # 1.5x sampling interval (15s max sensor-visual delta)


@dataclass
class TemporalValidationResult:
    """
    Structured temporal validation contract encapsulating multi-tier timestamps,
    synchronization metadata, frame age metrics, and temporal validity status.
    """
    timestamp: str
    time_sync_status: str              # "SYNCED", "UNSYNCED"
    clock_source: str                  # "NTP", "UNSYNCED_BOOT_TICK", "RTC", "UNKNOWN"
    capture_timestamp: str             # Moment of optical frame capture on camera hardware
    gateway_receive_timestamp: str     # Moment MQTT packet received by Gateway
    gateway_process_timestamp: str     # Moment frame processed in decision pipeline
    frame_age_ms: float                # (gateway_receive - capture) in milliseconds
    sensor_visual_delta_ms: Optional[float] = None  # |sensor_ts - capture_ts| in milliseconds
    temporal_valid: bool = False
    temporal_status: str = "INVALID"   # "VALID", "STALE", "FUTURE_TIMESTAMP", "CLOCK_SKEW", "UNSYNCED", "INVALID_TIMESTAMP"
    reason_code: str = "OK"            # "OK", "VISUAL_TIMESTAMP_INVALID", "VISUAL_TIMESTAMP_STALE", "VISUAL_TIMESTAMP_FUTURE", "VISUAL_CLOCK_UNSYNCED", "VISUAL_CLOCK_SKEW"
    monotonic_latency_ms: float = 0.0  # Measured strictly via time.perf_counter()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "time_sync_status": self.time_sync_status,
            "clock_source": self.clock_source,
            "capture_timestamp": self.capture_timestamp,
            "gateway_receive_timestamp": self.gateway_receive_timestamp,
            "gateway_process_timestamp": self.gateway_process_timestamp,
            "frame_age_ms": round(self.frame_age_ms, 2),
            "sensor_visual_delta_ms": round(self.sensor_visual_delta_ms, 2) if self.sensor_visual_delta_ms is not None else None,
            "temporal_valid": self.temporal_valid,
            "temporal_status": self.temporal_status,
            "reason_code": self.reason_code,
            "monotonic_latency_ms": round(self.monotonic_latency_ms, 2)
        }


class TemporalValidator:
    """
    Gateway-Side Temporal Consistency Validator (V4.8.3).
    Evaluates wall-clock provenance, synchronization status, frame age, future timestamps,
    and sensor-visual temporal alignment against configurable thresholds.
    """
    def __init__(
        self,
        max_allowed_frame_age_sec: float = MAX_ALLOWED_FRAME_AGE_SEC,
        max_future_tolerance_sec: float = MAX_FUTURE_TOLERANCE_SEC,
        max_sensor_visual_delta_sec: float = MAX_SENSOR_VISUAL_DELTA_SEC
    ):
        self.max_allowed_frame_age_sec = max_allowed_frame_age_sec
        self.max_future_tolerance_sec = max_future_tolerance_sec
        self.max_sensor_visual_delta_sec = max_sensor_visual_delta_sec

    def parse_iso_timestamp(self, ts_str: Optional[str]) -> Optional[datetime.datetime]:
        """Safely parses ISO-8601 timestamp string into timezone-aware/utc datetime."""
        if not ts_str or not isinstance(ts_str, str):
            return None
        try:
            # Handle trailing 'Z' for UTC
            clean_str = ts_str.rstrip("Z")
            dt = datetime.datetime.fromisoformat(clean_str)
            return dt
        except Exception:
            return None

    def validate_camera_frame_temporal(
        self,
        capture_ts_str: str,
        time_sync_status: str = "UNSYNCED",
        clock_source: str = "UNKNOWN",
        gateway_receive_ts_str: Optional[str] = None,
        gateway_process_ts_str: Optional[str] = None,
        sensor_ts_str: Optional[str] = None,
        start_monotonic: Optional[float] = None
    ) -> TemporalValidationResult:
        """
        Validates a camera frame's temporal integrity across capture, receive, and process points.
        Returns a TemporalValidationResult contract.
        """
        now_dt = datetime.datetime.now()
        now_iso = now_dt.isoformat()

        recv_iso = gateway_receive_ts_str or now_iso
        proc_iso = gateway_process_ts_str or now_iso

        # Measure monotonic latency if start_monotonic reference provided
        monotonic_latency_ms = 0.0
        if start_monotonic is not None:
            monotonic_latency_ms = (time.perf_counter() - start_monotonic) * 1000.0

        capture_dt = self.parse_iso_timestamp(capture_ts_str)
        recv_dt = self.parse_iso_timestamp(recv_iso) or now_dt
        proc_dt = self.parse_iso_timestamp(proc_iso) or now_dt

        # Check ISO timestamp syntax
        if capture_dt is None:
            return TemporalValidationResult(
                timestamp=capture_ts_str or now_iso,
                time_sync_status=time_sync_status,
                clock_source=clock_source,
                capture_timestamp=capture_ts_str or now_iso,
                gateway_receive_timestamp=recv_iso,
                gateway_process_timestamp=proc_iso,
                frame_age_ms=0.0,
                temporal_valid=False,
                temporal_status="INVALID_TIMESTAMP",
                reason_code="VISUAL_TIMESTAMP_INVALID",
                monotonic_latency_ms=monotonic_latency_ms
            )

        # Calculate frame age (receive_time - capture_time)
        frame_age_sec = (recv_dt - capture_dt).total_seconds()
        frame_age_ms = frame_age_sec * 1000.0

        # Calculate sensor-visual delta if sensor timestamp provided
        sensor_visual_delta_ms: Optional[float] = None
        if sensor_ts_str:
            sensor_dt = self.parse_iso_timestamp(sensor_ts_str)
            if sensor_dt:
                sensor_visual_delta_ms = abs((sensor_dt - capture_dt).total_seconds()) * 1000.0

        # Rule 1: Check unsynchronized device status
        if str(time_sync_status).upper() != "SYNCED":
            return TemporalValidationResult(
                timestamp=capture_ts_str,
                time_sync_status="UNSYNCED",
                clock_source=clock_source,
                capture_timestamp=capture_ts_str,
                gateway_receive_timestamp=recv_iso,
                gateway_process_timestamp=proc_iso,
                frame_age_ms=frame_age_ms,
                sensor_visual_delta_ms=sensor_visual_delta_ms,
                temporal_valid=False,
                temporal_status="UNSYNCED",
                reason_code="VISUAL_CLOCK_UNSYNCED",
                monotonic_latency_ms=monotonic_latency_ms
            )

        # Rule 2: Check future timestamp (capture_time > receive_time + tolerance)
        if frame_age_sec < -self.max_future_tolerance_sec:
            return TemporalValidationResult(
                timestamp=capture_ts_str,
                time_sync_status="SYNCED",
                clock_source=clock_source,
                capture_timestamp=capture_ts_str,
                gateway_receive_timestamp=recv_iso,
                gateway_process_timestamp=proc_iso,
                frame_age_ms=frame_age_ms,
                sensor_visual_delta_ms=sensor_visual_delta_ms,
                temporal_valid=False,
                temporal_status="FUTURE_TIMESTAMP",
                reason_code="VISUAL_TIMESTAMP_FUTURE",
                monotonic_latency_ms=monotonic_latency_ms
            )

        # Rule 3: Check stale frame age (frame_age > MAX_ALLOWED_FRAME_AGE_SEC)
        if frame_age_sec > self.max_allowed_frame_age_sec:
            return TemporalValidationResult(
                timestamp=capture_ts_str,
                time_sync_status="SYNCED",
                clock_source=clock_source,
                capture_timestamp=capture_ts_str,
                gateway_receive_timestamp=recv_iso,
                gateway_process_timestamp=proc_iso,
                frame_age_ms=frame_age_ms,
                sensor_visual_delta_ms=sensor_visual_delta_ms,
                temporal_valid=False,
                temporal_status="STALE",
                reason_code="VISUAL_TIMESTAMP_STALE",
                monotonic_latency_ms=monotonic_latency_ms
            )

        # Rule 4: Check sensor-visual delta skew if sensor timestamp present
        if sensor_visual_delta_ms is not None:
            if (sensor_visual_delta_ms / 1000.0) > self.max_sensor_visual_delta_sec:
                return TemporalValidationResult(
                    timestamp=capture_ts_str,
                    time_sync_status="SYNCED",
                    clock_source=clock_source,
                    capture_timestamp=capture_ts_str,
                    gateway_receive_timestamp=recv_iso,
                    gateway_process_timestamp=proc_iso,
                    frame_age_ms=frame_age_ms,
                    sensor_visual_delta_ms=sensor_visual_delta_ms,
                    temporal_valid=False,
                    temporal_status="CLOCK_SKEW",
                    reason_code="VISUAL_CLOCK_SKEW",
                    monotonic_latency_ms=monotonic_latency_ms
                )

        # All temporal validity rules passed!
        return TemporalValidationResult(
            timestamp=capture_ts_str,
            time_sync_status="SYNCED",
            clock_source=clock_source,
            capture_timestamp=capture_ts_str,
            gateway_receive_timestamp=recv_iso,
            gateway_process_timestamp=proc_iso,
            frame_age_ms=frame_age_ms,
            sensor_visual_delta_ms=sensor_visual_delta_ms,
            temporal_valid=True,
            temporal_status="VALID",
            reason_code="OK",
            monotonic_latency_ms=monotonic_latency_ms
        )
