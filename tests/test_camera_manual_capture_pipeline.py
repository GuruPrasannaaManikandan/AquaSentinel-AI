"""
test_camera_manual_capture_pipeline.py
======================================
Automated test suite verifying the ESP32-CAM manual capture display pipeline:
1. POST /api/camera/capture returns success==True, non-empty image_base64, frame_sequence, sensor=="GC2145"
2. Consecutive captures produce strictly monotonically increasing frame sequence values (N -> N+1)
3. Decoded image bytes are valid JPEG (magic bytes 0xFF 0xD8) and verifiable by PIL
4. Atomic metadata concordance between frame sequence, timestamp, and payload
5. MobileNetV3 optical intelligence inference output structure
"""

import os
import io
import base64
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from src.backend.app import app
from src.cv.physical_camera_service import camera_service


client = TestClient(app)


def test_01_camera_status():
    """Verify camera operational status endpoint."""
    resp = client.get("/api/camera/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["camera"] == "ESP32-CAM"
    assert data["sensor"] == "GC2145"
    assert data["source"] == "PHYSICAL_ESP32_CAM"
    assert "frame_sequence" in data


def test_02_single_capture_response_contract():
    """Verify single photo capture returns required schema with image_base64 and GC2145 metadata."""
    resp = client.post("/api/camera/capture?device_id=AQUA_FRESH_001")
    assert resp.status_code == 200
    data = resp.json()

    assert data.get("success") in [True, 1]
    assert data.get("sensor") == "GC2145"
    assert data.get("camera") == "ESP32-CAM"
    assert "frame_sequence" in data
    assert isinstance(data["frame_sequence"], int)
    assert "capture_id" in data
    assert "timestamp" in data
    assert "captured_at" in data

    # Validate image_base64 presence and decode
    b64 = data.get("image_base64")
    assert b64 is not None and len(b64) > 100

    raw_bytes = base64.b64decode(b64)
    assert len(raw_bytes) > 100
    assert raw_bytes.startswith(b"\xff\xd8") or raw_bytes.startswith(b"\xff\xd8\xff")

    # PIL verification
    img = Image.open(io.BytesIO(raw_bytes))
    img.verify()
    assert img.format in ["JPEG", "MPO"]


def test_03_consecutive_captures_strictly_increasing_sequence():
    """Verify that consecutive captures produce strictly increasing frame sequences (N -> N+1)."""
    resp1 = client.post("/api/camera/capture?device_id=AQUA_FRESH_001")
    assert resp1.status_code == 200
    data1 = resp1.json()
    seq1 = data1["frame_sequence"]

    resp2 = client.post("/api/camera/capture?device_id=AQUA_FRESH_001")
    assert resp2.status_code == 200
    data2 = resp2.json()
    seq2 = data2["frame_sequence"]

    assert seq2 > seq1, f"Frame sequence did not increment: seq1={seq1}, seq2={seq2}"
    assert seq2 == seq1 + 1, f"Expected step of 1: seq1={seq1}, seq2={seq2}"


def test_04_camera_latest_endpoint_concordance():
    """Verify GET /api/camera/latest reflects the newly captured frame metadata."""
    resp_cap = client.post("/api/camera/capture?device_id=AQUA_FRESH_001")
    assert resp_cap.status_code == 200
    cap_data = resp_cap.json()

    resp_latest = client.get("/api/camera/latest")
    assert resp_latest.status_code == 200
    latest_data = resp_latest.json()

    assert latest_data["frame_sequence"] == cap_data["frame_sequence"]
    assert latest_data["capture_id"] == cap_data["capture_id"]
    assert latest_data["captured_at"] == cap_data["captured_at"]


def test_05_optical_intelligence_inference():
    """Verify that capture automatically invokes edge vision inference pipeline."""
    resp = client.post("/api/camera/capture?device_id=AQUA_FRESH_001")
    assert resp.status_code == 200
    data = resp.json()

    assert "optical_intelligence" in data
    opt = data["optical_intelligence"]
    assert opt.get("status") == "SUCCESS"
    assert "MobileNetV3" in opt.get("model_name", "")
    assert "predicted_class" in opt
    assert "visual_state" in opt
    assert "confidence" in opt
