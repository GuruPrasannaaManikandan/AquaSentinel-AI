import os
import json
import datetime
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import math

from src.backend.services import BackendService
from src.backend.schemas import (
    DeviceInfoSchema, TelemetryPayloadSchema, FusionDecisionSchema, ActuatorStateSchema,
    AlertSchema, CommandRequestSchema, SimulationControlSchema, SystemStatusSchema
)

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
    # Construct schema-valid json frame
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Check if loop is running
    if loop.is_running():
        asyncio.run_coroutine_threadsafe(
            manager.broadcast({"type": "telemetry", "data": payload}), loop
        )
    else:
        loop.run_until_complete(
            manager.broadcast({"type": "telemetry", "data": payload})
        )

def handle_live_decision(payload):
    import asyncio
    # Append current actuator state
    device_id = payload["device_id"]
    device = service.runtime.devices[device_id]
    payload["actuator_summary"] = device.actuators.get_summary()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        asyncio.run_coroutine_threadsafe(
            manager.broadcast({"type": "decision", "data": payload}), loop
        )
    else:
        loop.run_until_complete(
            manager.broadcast({"type": "decision", "data": payload})
        )

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
    """Lists registered virtual aquatic monitoring devices."""
    devices = []
    for d_id, profile in service.runtime.gateway.device_registry["devices"].items():
        dev_obj = service.runtime.devices.get(d_id)
        status = dev_obj.state if dev_obj else profile["status"]
        devices.append(DeviceInfoSchema(
            device_id=d_id,
            ecosystem_type=profile["ecosystem_type"],
            dataset_route=profile["dataset_route"],
            location=profile["location"],
            enabled_sensors=profile["enabled_sensors"],
            firmware_version=profile["firmware_version"],
            status=status
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
    status = dev_obj.state if dev_obj else profile["status"]
    
    return DeviceInfoSchema(
        device_id=device_id,
        ecosystem_type=profile["ecosystem_type"],
        dataset_route=profile["dataset_route"],
        location=profile["location"],
        enabled_sensors=profile["enabled_sensors"],
        firmware_version=profile["firmware_version"],
        status=status
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

@app.get("/devices/{device_id}/telemetry", tags=["Data Logs"])
def get_device_telemetry(
    device_id: str = Path(...),
    start_time: Optional[str] = Query(None, description="ISO format start window"),
    end_time: Optional[str] = Query(None, description="ISO format end window")
):
    """Retrieves time-series telemetry logs stored for the device."""
    registry = service.runtime.gateway.device_registry["devices"]
    if device_id not in registry:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found.")
    return service.event_store.get_historical_telemetry(device_id, start_time, end_time)

@app.get("/devices/{device_id}/decisions", tags=["Data Logs"])
def get_device_decisions(
    device_id: str = Path(...),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None)
):
    """Retrieves time-series fusion decisions for the device."""
    registry = service.runtime.gateway.device_registry["devices"]
    if device_id not in registry:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found.")
    return service.event_store.get_historical_decisions(device_id, start_time, end_time)

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

@app.get("/alerts", response_model=List[AlertSchema], tags=["Alerts"])
def get_alerts(
    device_id: Optional[str] = Query(None),
    acknowledged: Optional[bool] = Query(None)
):
    """Lists persisted warning, critical, and OOD alerts."""
    return service.event_store.get_alerts(device_id, acknowledged)

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
        service.send_device_command(device_id, body.command, body.payload)
        return {"status": "SUCCESS", "message": f"Command {body.command} dispatched to {device_id}."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
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
