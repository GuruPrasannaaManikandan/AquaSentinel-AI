from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class DeviceInfoSchema(BaseModel):
    device_id: str
    ecosystem_type: str
    dataset_route: str
    location: Dict[str, float]
    enabled_sensors: List[str]
    firmware_version: str
    status: str

class LocationSchema(BaseModel):
    latitude: float
    longitude: float

class SensorsSchema(BaseModel):
    temperature_c: Optional[float] = None
    salinity_ppt: Optional[float] = None
    ph: Optional[float] = None
    turbidity_ntu: Optional[float] = None
    dissolved_oxygen_mg_l: Optional[float] = None

class DeviceHealthSchema(BaseModel):
    wifi_connected: bool
    mqtt_connected: bool
    sensor_status: str

class TelemetryPayloadSchema(BaseModel):
    schema_version: str
    device_id: str
    timestamp: str
    provenance_timestamp: Optional[str] = None
    dataset_route: str
    location: LocationSchema
    sensors: SensorsSchema
    device_health: DeviceHealthSchema

class MLEvidenceSchema(BaseModel):
    predicted_class: Any
    confidence: float
    dangerous_class: bool
    model_id: str

class AISEvidenceSchema(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    matched_detector_count: int
    nearest_detector_distance: float
    ais_model_id: str

class FusionDetailsSchema(BaseModel):
    final_state: str
    reason_code: str
    reasoning: str
    confidence_band: str

class SystemMetadataSchema(BaseModel):
    fusion_version: str

class FusionDecisionSchema(BaseModel):
    timestamp: str
    device_id: str
    ml_evidence: MLEvidenceSchema
    ais_evidence: AISEvidenceSchema
    fusion: FusionDetailsSchema
    system_metadata: SystemMetadataSchema

class ActuatorStateSchema(BaseModel):
    timestamp: str
    device_id: str
    green_led: str
    yellow_led: str
    red_led: str
    buzzer: str
    pump_relay: str
    event_desc: str

class AlertSchema(BaseModel):
    id: Optional[int] = None
    timestamp: str
    device_id: str
    severity: str
    message: str
    reason_code: str
    acknowledged: int

class CommandRequestSchema(BaseModel):
    command: str = Field(..., description="Action command e.g., ACTIVATE_BUZZER, RESTART_DEVICE, etc.")
    payload: Optional[Dict[str, Any]] = None

class SimulationControlSchema(BaseModel):
    device_id: str
    scenario: str

class SystemStatusSchema(BaseModel):
    active_devices_count: int
    total_telemetry_records: int
    total_warnings: int
    total_criticals: int
    total_anomalies: int
    unacknowledged_alerts_count: int
    gateway_status: str
