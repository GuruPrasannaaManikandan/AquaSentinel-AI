import os
import json
import datetime
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, FileResponse
from typing import List, Dict, Any, Optional
from src.cv.physical_camera_service import camera_service, CAPTURES_DIR, BASE_DIR

import numpy as np
import pandas as pd
import math

from src.backend.services import BackendService
from src.backend.schemas import (
    DeviceInfoSchema, TelemetryPayloadSchema, FusionDecisionSchema, ActuatorStateSchema,
    AlertSchema, CommandRequestSchema, SimulationControlSchema, SystemStatusSchema
)
from src.fusion.explainability import ExplainabilityEngine
from src.iot.historical_intelligence import HistoricalIntelligenceEngine

explainer = ExplainabilityEngine()
historical_engine = HistoricalIntelligenceEngine()

def sanitize_json_data(data: Any) -> Any:
    if data is None or data is pd.NA:
        return None

    # Handle float / numpy float
    if isinstance(data, (float, np.floating)):
        val = float(data)
        if not math.isfinite(val):
            return None
        return val

    # Handle int / numpy integer
    if isinstance(data, (int, np.integer)):
        return int(data)

    # Handle NumPy arrays
    if isinstance(data, np.ndarray):
        return [sanitize_json_data(x) for x in data.tolist()]

    # Handle dict
    if isinstance(data, dict):
        return {k: sanitize_json_data(v) for k, v in data.items()}

    # Handle list or tuple
    if isinstance(data, (list, tuple)):
        return [sanitize_json_data(x) for x in data]

    # Handle pandas series / dataframe by converting to list / dict
    if isinstance(data, pd.Series):
        return [sanitize_json_data(x) for x in data.tolist()]
    if isinstance(data, pd.DataFrame):
        return sanitize_json_data(data.to_dict(orient="records"))

    # Check if pandas says it is NA (e.g. for any other pandas scalar types)
    try:
        if pd.isna(data):
            return None
    except Exception:
        pass

    return data

class SafeJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        sanitized = sanitize_json_data(content)
        return super().render(sanitized)

app = FastAPI(
    title="Aquatic Ecosystem IoT & AIS Monitoring Gateway Backend",
    version="1.0.0",
    description="REST API and WebSocket server coordinating the IoT simulated nodes, gateway validations, and evidence-fusion engine.",
    default_response_class=SafeJSONResponse
)

# Enable CORS for frontend dashboard communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services singleton
service = BackendService.get_instance()

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # Clean up dead connections
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        
        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()

# Hook backend service callbacks to broadcast to WebSockets
def handle_live_telemetry(payload):
    if not manager.active_connections:
        return
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(
            manager.broadcast({"type": "telemetry", "data": payload}), loop
        )
    else:
        try:
            asyncio.run(manager.broadcast({"type": "telemetry", "data": payload}))
        except Exception:
            pass

def handle_live_decision(payload):
    if not manager.active_connections:
        return
    import asyncio
    device_id = payload.get("device_id")
    if device_id and device_id in service.runtime.devices:
        device = service.runtime.devices[device_id]
        payload["actuator_summary"] = device.actuators.get_summary()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(
            manager.broadcast({"type": "decision", "data": payload}), loop
        )
    else:
        try:
            asyncio.run(manager.broadcast({"type": "decision", "data": payload}))
        except Exception:
            pass

service.register_telemetry_callback(handle_live_telemetry)
service.register_decision_callback(handle_live_decision)


# --- REST ENDPOINTS ---

@app.get("/health", tags=["System"])
def get_health():
    """Returns database health status and model availability checks."""
    try:
        # Check SQLite connection
        conn = service.event_store.db_path
        db_ok = os.path.exists(conn)
        
        # Check model loaded
        caml_loaded = "caml" in service.runtime.gateway.pipeline.ml_loader.models
        habsos_loaded = "habsos" in service.runtime.gateway.pipeline.ml_loader.models

        return {
            "status": "UP",
            "timestamp": datetime.datetime.now().isoformat(),
            "event_store": "OK" if db_ok else "OFFLINE",
            "models": {
                "caml_loaded": caml_loaded,
                "habsos_loaded": habsos_loaded
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")

@app.get("/devices", response_model=List[DeviceInfoSchema], tags=["Devices"])
def get_devices():
    """Lists registered virtual and physical aquatic monitoring devices."""
    devices = []
    for d_id, profile in service.runtime.gateway.device_registry["devices"].items():
        dev_obj = service.runtime.devices.get(d_id)
        fw = "3.8.1" if d_id == "AQUA_FRESH_001" else profile.get("firmware_version", "1.0.0")
        st = "MONITORING" if d_id == "AQUA_FRESH_001" else (dev_obj.state if dev_obj else profile["status"])
        devices.append(DeviceInfoSchema(
            device_id=d_id,
            ecosystem_type=profile["ecosystem_type"],
            dataset_route=profile["dataset_route"],
            location=profile["location"],
            enabled_sensors=profile["enabled_sensors"],
            firmware_version=fw,
            status=st
        ))
    return devices

@app.get("/devices/{device_id}", response_model=DeviceInfoSchema, tags=["Devices"])
def get_device(device_id: str = Path(..., description="Device ID e.g. AQUA_FRESH_001")):
    """Retrieves metadata registry entry for a specific device."""
    registry = service.runtime.gateway.device_registry["devices"]
    if device_id not in registry:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found.")
    profile = registry[device_id]
    dev_obj = service.runtime.devices.get(device_id)
    fw = "3.8.1" if device_id == "AQUA_FRESH_001" else profile.get("firmware_version", "1.0.0")
    st = "MONITORING" if device_id == "AQUA_FRESH_001" else (dev_obj.state if dev_obj else profile["status"])
    
    return DeviceInfoSchema(
        device_id=device_id,
        ecosystem_type=profile["ecosystem_type"],
        dataset_route=profile["dataset_route"],
        location=profile["location"],
        enabled_sensors=profile["enabled_sensors"],
        firmware_version=fw,
        status=st
    )

@app.get("/devices/{device_id}/latest", tags=["Devices"])
def get_latest_device_telemetry_and_decision(device_id: str = Path(...)):
    """Retrieves the latest telemetry and corresponding decision for a device."""
    registry = service.runtime.gateway.device_registry["devices"]
    if device_id not in registry:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found.")

    telemetry = service.event_store.get_latest_telemetry(device_id)
    decision = None
    if telemetry:
        decision = service.event_store.get_decision_by_timestamp(device_id, telemetry["timestamp"])
        if decision:
            actuator = service.event_store.get_actuators_by_timestamp(device_id, telemetry["timestamp"])
            if actuator:
                decision["actuator_summary"] = actuator["summary"]
            else:
                decision["actuator_summary"] = "LEDs(G=OFF, Y=OFF, R=OFF), Buzzer=OFF, Pump=OFF"
        else:
            is_fault = (telemetry["sensor_status"] == "FAULT")
            decision = {
                "device_id": device_id,
                "timestamp": telemetry["timestamp"],
                "ml_predicted_class": "UNAVAILABLE",
                "ml_confidence": 0.0,
                "ml_dangerous_class": 0,
                "ml_model_id": "UNAVAILABLE",
                "ais_is_anomaly": 1,
                "ais_anomaly_score": 1.0,
                "ais_matched_detectors": 0,
                "ais_nearest_distance": 0.0,
                "ais_model_id": "UNAVAILABLE",
                "final_state": "SENSOR_FAULT" if is_fault else "NORMAL",
                "reason_code": "SENSOR_FAULT_BYPASS" if is_fault else "ML_NORMAL_AIS_NORMAL",
                "reasoning": "Telemetry flagged with sensor fault status. Model inference bypassed." if is_fault else "Telemetry exists but decision is not processed.",
                "confidence_band": "LOW",
                "fusion_version": "1.0.0",
                "actuator_summary": "LEDs(G=OFF, Y=ON, R=ON), Buzzer=ON, Pump=OFF" if is_fault else "LEDs(G=ON, Y=OFF, R=OFF), Buzzer=OFF, Pump=OFF"
            }

    return {
        "device_id": device_id,
        "telemetry": telemetry,
        "decision": decision
    }

@app.get("/devices/{device_id}/intelligence", tags=["Intelligence"])
def get_device_intelligence(device_id: str = Path(...)):
    """Provides V5 Explainability, Modality Attribution, Digital State Baselines, and Temporal Trajectory."""
    registry = service.runtime.gateway.device_registry["devices"]
    if device_id not in registry:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found.")

    telemetry = getattr(service.runtime.gateway, 'latest_telemetries', {}).get(device_id) or service.event_store.get_latest_telemetry(device_id)
    decision = service.runtime.gateway.latest_decisions.get(device_id) or service.event_store.get_latest_decision(device_id)

    sensors = {}
    if telemetry:
        if isinstance(telemetry.get("sensors"), dict):
            sensors = telemetry["sensors"]
        else:
            sensors = {
                "ph": telemetry.get("ph"),
                "turbidity_ntu": telemetry.get("turbidity_ntu"),
                "temperature_c": telemetry.get("temperature_c"),
                "salinity_ppt": telemetry.get("salinity_ppt"),
                "dissolved_oxygen_mg_l": telemetry.get("dissolved_oxygen_mg_l")
            }
    digital_state = historical_engine.update_and_evaluate(device_id, sensors, decision=decision).to_dict()

    explanation = None
    if decision:
        explanation = explainer.explain(decision, device_id=device_id).to_dict()

    sensor_q = decision.get("sensor_quality") if decision else None
    if not sensor_q and telemetry and sensors:
        try:
            sensor_q = service.runtime.gateway.quality_evaluator.evaluate(
                sensors, timestamp=telemetry.get("timestamp"), device_id=device_id
            ).to_dict()
        except Exception:
            sensor_q = None

    temporal_ev = decision.get("temporal_evidence") if decision else None
    if not temporal_ev and telemetry:
        try:
            hist = service.event_store.get_historical_telemetry(device_id, limit=12)
            if hist:
                for row in hist:
                    s_hist = row.get("sensors") or {
                        "ph": row.get("ph"),
                        "turbidity_ntu": row.get("turbidity_ntu"),
                        "turbidity_voltage": row.get("turbidity_voltage") or row.get("turbidity_ntu"),
                        "temperature_c": row.get("temperature_c"),
                        "salinity_ppt": row.get("salinity_ppt"),
                        "dissolved_oxygen_mg_l": row.get("dissolved_oxygen_mg_l")
                    }
                    s_hist["timestamp"] = row.get("timestamp")
                    t_res = service.runtime.gateway.temporal_engine.evaluate_telemetry(device_id, s_hist)
                temporal_ev = t_res.to_dict()
        except Exception:
            temporal_ev = None

    vis_ev = (decision.get("visual_evidence") if decision else None) or getattr(service.runtime.gateway, 'latest_visual_evidence', {}).get(device_id)

    fusion_data = decision.get("fusion") if decision else None
    if not fusion_data and decision:
        fusion_data = {
            "ecological_state": decision.get("final_state", "NORMAL"),
            "composite_risk_score": decision.get("composite_risk_score", 0.0),
            "reason_code": decision.get("reason_code", "NORMAL"),
            "confidence_band": decision.get("confidence_band", "LOW")
        }

    return sanitize_json_data({
        "device_id": device_id,
        "explanation": explanation,
        "digital_state": digital_state,
        "temporal_evidence": temporal_ev,
        "sensor_quality": sensor_q,
        "visual_evidence": vis_ev,
        "fusion": fusion_data,
        "multimodal_intelligence": decision.get("multimodal_intelligence") if decision else None,
        "multimodal_snapshot": decision.get("multimodal_snapshot") if decision else None,
        "concordance": decision.get("concordance") if decision else None,
        "conflict": decision.get("conflict") if decision else None,
        "multimodal_state": decision.get("multimodal_state") if decision else None
    })

@app.get("/devices/{device_id}/multimodal", tags=["Intelligence"])
def get_device_multimodal(device_id: str = Path(...)):
    """Retrieves comprehensive V7 Multimodal Alignment, Concordance, Conflict, and Dominance State."""
    registry = service.runtime.gateway.device_registry["devices"]
    if device_id not in registry:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found.")

    decision = service.runtime.gateway.latest_decisions.get(device_id)
    latest_event = service.event_store.get_latest_multimodal_event(device_id)
    history = service.event_store.get_multimodal_history(device_id, limit=20)

    return sanitize_json_data({
        "device_id": device_id,
        "active_decision_multimodal": decision.get("multimodal_intelligence") if decision else None,
        "concordance": decision.get("concordance") if decision else None,
        "conflict": decision.get("conflict") if decision else None,
        "multimodal_snapshot": decision.get("multimodal_snapshot") if decision else None,
        "multimodal_state": decision.get("multimodal_state") if decision else None,
        "latest_persisted_event": latest_event,
        "recent_history": history
    })

@app.get("/devices/{device_id}/response", tags=["Autonomous Response"])
def get_device_autonomous_response(device_id: str = Path(...)):
    """Retrieves active V8 autonomous response policy and actuator safety audit records."""
    registry = service.runtime.gateway.device_registry["devices"]
    if device_id not in registry:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found.")

    decision = service.runtime.gateway.latest_decisions.get(device_id)
    cached_actuator_decision = service.runtime.gateway.latest_actuator_decision.get(device_id)
    latest_event = service.event_store.get_latest_actuator_decision(device_id)
    history = service.event_store.get_actuator_decisions(device_id, limit=20)

    return sanitize_json_data({
        "device_id": device_id,
        "policy_state": decision.get("autonomous_policy") if decision else "MONITOR",
        "actuator_decision": cached_actuator_decision or latest_event,
        "recent_actuator_history": history
    })

@app.get("/devices/{device_id}/risk-trend", tags=["Predictive Intelligence"])
def get_device_risk_trend(device_id: str = Path(...)):
    """Retrieves active V8 risk trajectory and interpretable early-warning horizon."""
    registry = service.runtime.gateway.device_registry["devices"]
    if device_id not in registry:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found.")

    decision = service.runtime.gateway.latest_decisions.get(device_id)
    cached_trend = service.runtime.gateway.latest_risk_trend.get(device_id)
    latest_event = service.event_store.get_latest_risk_trend(device_id)
    history = service.event_store.get_risk_trend_history(device_id, limit=20)

    return sanitize_json_data({
        "device_id": device_id,
        "risk_trend": cached_trend or (decision.get("risk_trend") if decision else None) or latest_event,
        "recent_trend_history": history
    })

@app.get("/system/reliability", tags=["Observability"])
def get_system_reliability_metrics():
    """Retrieves system-wide throughput, latency percentiles, and reliability metrics."""
    from src.utils.observability import observability_collector
    return sanitize_json_data(observability_collector.get_summary_metrics())


@app.post("/devices/{device_id}/frame", tags=["Camera"])
def ingest_device_frame(
    device_id: str = Path(...),
    payload: Dict[str, Any] = Body(...)
):
    """
    Ingests an ESP32-CAM frame in Base64 JPEG format.
    Processes optical quality, executes MobileNetV3 visual inference,
    updates gateway latest_visual_evidence, and returns structured VisualDetectionResult.
    """
    img_b64 = payload.get("image_base64") or payload.get("image_b64", "")
    ts = payload.get("timestamp") or datetime.datetime.now(datetime.timezone.utc).isoformat()
    fid = payload.get("frame_id")

    gateway = service.runtime.gateway
    try:
        vis_dict = gateway.process_camera_frame(
            device_id=device_id,
            frame_bytes_or_b64=img_b64,
            timestamp=ts,
            frame_id=fid
        )
        return sanitize_json_data({
            "status": "SUCCESS",
            "device_id": device_id,
            "frame_id": vis_dict.get("frame_id"),
            "timestamp": vis_dict.get("timestamp"),
            "predicted_class": vis_dict.get("class_name") or vis_dict.get("predicted_visual_class"),
            "evidence_state": vis_dict.get("evidence_state") or vis_dict.get("visual_state"),
            "q_visual": vis_dict.get("q_visual", 1.0),
            "effective_confidence": vis_dict.get("effective_confidence", 0.0),
            "risk_level": vis_dict.get("risk_level", "UNKNOWN"),
            "visual_evidence": vis_dict
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Frame processing error: {e}")

@app.get("/devices/{device_id}/telemetry", tags=["Data Logs"])
def get_device_telemetry(
    device_id: str = Path(...),
    start_time: Optional[str] = Query(None, description="ISO format start window"),
    end_time: Optional[str] = Query(None, description="ISO format end window"),
    limit: Optional[int] = Query(None, description="Limit max records returned")
):
    """Retrieves time-series telemetry logs stored for the device."""
    registry = service.runtime.gateway.device_registry["devices"]
    if device_id not in registry:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found.")
    return service.event_store.get_historical_telemetry(device_id, start_time, end_time, limit=limit)

@app.get("/devices/{device_id}/decisions", tags=["Data Logs"])
def get_device_decisions(
    device_id: str = Path(...),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, description="Limit max records returned")
):
    """Retrieves time-series fusion decisions for the device."""
    registry = service.runtime.gateway.device_registry["devices"]
    if device_id not in registry:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found.")
    return service.event_store.get_historical_decisions(device_id, start_time, end_time, limit=limit)

@app.get("/devices/{device_id}/actuators", tags=["Data Logs"])
def get_device_actuators(
    device_id: str = Path(...),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None)
):
    """Retrieves time-series actuator logs for the device."""
    registry = service.runtime.gateway.device_registry["devices"]
    if device_id not in registry:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found.")
    return service.event_store.get_historical_actuators(device_id, start_time, end_time)

LIVE_SENSOR_PATH = os.path.join(BASE_DIR, "data", "live_sensor.json")


@app.get("/api/sensors/live", tags=["Sensors"])
def get_live_sensor_reading():
    """
    Latest physical reading from the sensor ESP32 (pH + turbidity), as written by
    scripts/live_mqtt_gateway_bridge.py. `stale` is true when the bridge has not
    received anything for 10 seconds (board unplugged or bridge not running).
    """
    if not os.path.exists(LIVE_SENSOR_PATH):
        return {"available": False, "reason": "No reading yet. Start scripts/live_mqtt_gateway_bridge.py with the sensor ESP32 plugged in."}
    try:
        with open(LIVE_SENSOR_PATH, "r") as f:
            reading = json.load(f)
    except Exception as e:
        return {"available": False, "reason": f"Could not read live sensor file: {e}"}
    age = None
    try:
        received = datetime.datetime.fromisoformat(reading.get("received_at"))
        age = (datetime.datetime.now(datetime.timezone.utc) - received).total_seconds()
    except Exception:
        pass
    reading["available"] = True
    reading["age_sec"] = round(age, 1) if age is not None else None
    reading["stale"] = age is None or age > 10.0
    return sanitize_json_data(reading)


@app.post("/api/camera/capture", tags=["Camera"])
@app.post("/camera/capture", tags=["Camera"])
def capture_physical_camera_photo(
    device_id: Optional[str] = Query("AQUA_FRESH_001", description="Device ID to bind capture evidence to")
):
    """
    Triggers ONE manual hardware acquisition from the physical ESP32-CAM (GC2145, port auto-detected).
    Enforces fresh-frame guarantee, saves image to data/camera_captures/,
    evaluates optical intelligence via gateway, and returns structured JSON metadata.
    """
    ok, res = camera_service.capture_single_photo(timeout_sec=15.0)
    if not ok:
        return JSONResponse(status_code=400, content=sanitize_json_data(res))

    target_dev = device_id or "AQUA_FRESH_001"
    vis_dict = None
    try:
        gateway = service.runtime.gateway
        vis_dict = gateway.process_camera_frame(
            device_id=target_dev,
            frame_bytes_or_b64=res.get("image_base64", ""),
            timestamp=res.get("timestamp"),
            frame_id=res.get("capture_id")
        )
    except Exception as e:
        print(f"[BACKEND-CAM] Optical inference pipeline note: {e}")

    if vis_dict:
        res["optical_intelligence"] = {
            "status": "SUCCESS",
            "model_name": vis_dict.get("model_name", "MobileNetV3-Small-AquaticBloom"),
            "predicted_class": vis_dict.get("class_name") or vis_dict.get("predicted_visual_class") or "UNAVAILABLE",
            "visual_state": vis_dict.get("evidence_state") or vis_dict.get("visual_state") or "UNCERTAIN",
            "confidence": vis_dict.get("confidence", 0.0),
            "effective_confidence": vis_dict.get("effective_confidence", 0.0),
            "q_visual": vis_dict.get("q_visual", 1.0),
            "quality_state": vis_dict.get("quality_state", "RELIABLE"),
            "optical_quality": vis_dict.get("optical_quality", {})
        }
    else:
        res["optical_intelligence"] = {
            "status": "UNAVAILABLE",
            "message": "Optical classification unavailable"
        }

    return sanitize_json_data(res)


@app.post("/devices/{device_id}/camera/capture", tags=["Camera"])
def capture_physical_camera_photo_device(
    device_id: str = Path(..., description="Device ID")
):
    return capture_physical_camera_photo(device_id=device_id)



@app.get("/api/camera/status", tags=["Camera"])
@app.get("/camera/status", tags=["Camera"])
def get_camera_status():
    """Returns the operational status of the physical ESP32-CAM node."""
    return sanitize_json_data(camera_service.get_status())


@app.get("/api/camera/latest", tags=["Camera"])
@app.get("/camera/latest", tags=["Camera"])
def get_camera_latest():
    """Returns the latest captured frame metadata."""
    meta = camera_service.last_capture_meta
    if not meta:
        return {"success": False, "status": "NO_CAPTURES_YET", "camera": "ESP32-CAM", "sensor": "GC2145"}
    return sanitize_json_data(meta)


@app.get("/api/camera/image/latest", tags=["Camera"])
@app.get("/camera/image/latest", tags=["Camera"])
def get_latest_camera_image():
    """Serves the latest captured JPEG image bytes."""
    meta = camera_service.last_capture_meta
    if meta and os.path.exists(meta.get("absolute_path", "")):
        return FileResponse(meta["absolute_path"], media_type="image/jpeg")
    docs_path = os.path.join(BASE_DIR, "docs", "LIVE_ESP32_CAM_GC2145_FRAME.jpg")
    if os.path.exists(docs_path):
        return FileResponse(docs_path, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="No camera frames captured yet.")


@app.get("/api/camera/captures/{filename}", tags=["Camera"])
@app.get("/camera/captures/{filename}", tags=["Camera"])
def get_capture_image_by_filename(filename: str = Path(...)):
    """Serves a specific captured JPEG image from data/camera_captures/."""
    file_path = os.path.join(CAPTURES_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail=f"Image {filename} not found.")


@app.get("/alerts", response_model=List[AlertSchema], tags=["Alerts"])
def get_alerts(
    device_id: Optional[str] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    limit: Optional[int] = Query(None, description="Limit max alerts returned")
):
    """Lists persisted warning, critical, and OOD alerts."""
    return service.event_store.get_alerts(device_id, acknowledged, limit=limit)

@app.post("/alerts/{alert_id}/acknowledge", tags=["Alerts"])
def acknowledge_alert(alert_id: int = Path(...)):
    """Acknowledges a logged alert by ID."""
    service.event_store.acknowledge_alert(alert_id)
    return {"status": "SUCCESS", "message": f"Alert {alert_id} acknowledged."}

@app.get("/system/status", response_model=SystemStatusSchema, tags=["System"])
def get_system_status():
    """Aggregates overview KPIs across the entire ecosystem."""
    stats = service.event_store.get_device_stats()
    unack_alerts = len(service.event_store.get_alerts(acknowledged=False))
    
    return SystemStatusSchema(
        active_devices_count=len(service.runtime.devices),
        total_telemetry_records=stats["total_telemetry"],
        total_warnings=stats["total_warnings"],
        total_criticals=stats["total_criticals"],
        total_anomalies=stats["total_anomalies"],
        unacknowledged_alerts_count=unack_alerts,
        gateway_status="ACTIVE"
    )

@app.post("/devices/{device_id}/command", tags=["Controls"])
def post_device_command(
    device_id: str = Path(...),
    body: CommandRequestSchema = Body(...)
):
    """Dispatches override instructions (buzzers, pumps, sampling rates) to devices."""
    try:
        cmd_result = service.send_device_command(device_id, body.command, body.payload)
        return {
            "status": "SUCCESS",
            "execution_status": "COMMAND_COMPLETED",
            "command": body.command,
            "device_id": device_id,
            "result": cmd_result,
            "message": cmd_result.get("message", f"Command {body.command} executed successfully.") if isinstance(cmd_result, dict) else f"Command {body.command} dispatched to {device_id}."
        }
    except ValueError as e:
        status_code = 400 if "interval" in str(e).lower() else 404
        raise HTTPException(status_code=status_code, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Device {device_id} network is offline: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulation/start", tags=["Simulation"])
def post_simulation_start():
    """Starts background simulation loop thread."""
    started = service.start_simulation()
    return {
        "status": "SUCCESS" if started else "ALREADY_RUNNING",
        "message": "Background simulation started." if started else "Simulation is already active."
    }

@app.post("/simulation/stop", tags=["Simulation"])
def post_simulation_stop():
    """Stops background simulation loop thread."""
    stopped = service.stop_simulation()
    return {
        "status": "SUCCESS" if stopped else "ALREADY_STOPPED",
        "message": "Background simulation stopped." if stopped else "Simulation is already idle."
    }

@app.get("/simulation/scenarios", tags=["Simulation"])
def get_simulation_scenarios():
    """Retrieves the active scenario configuration for all devices."""
    return service.scenarios

@app.post("/simulation/scenario", tags=["Simulation"])
def post_simulation_scenario(body: SimulationControlSchema = Body(...)):
    """Sets a device's simulated physical scenario state and triggers an immediate cycle."""
    try:
        service.set_scenario(body.device_id, body.scenario)
        results = service._execute_cycle_locked(force=True)
        return {
            "status": "SUCCESS",
            "message": f"Scenario for {body.device_id} updated to {body.scenario}.",
            "results": results
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/simulation/cycle", tags=["Simulation"])
def post_simulation_cycle():
    """Triggers exactly one synchronous poll-inference-fused cycle across all devices."""
    try:
        results = service.run_single_cycle()
        return {
            "status": "SUCCESS",
            "message": "Single cycle simulation step completed.",
            "results": results
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation cycle failed: {e}")


# --- WEBSOCKET ENDPOINT ---

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection streaming real-time telemetry, model outputs, and state changes."""
    await manager.connect(websocket)
    try:
        # Send initial registration message
        await websocket.send_json({"type": "status", "message": "WebSocket connection established."})
        
        # Keep connection open
        while True:
            # Wait for text/heartbeat from client
            data = await websocket.receive_text()
            # Respond to ping/heartbeats
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
