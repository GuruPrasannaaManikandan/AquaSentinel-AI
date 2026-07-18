import os
import json
import datetime
import pandas as pd
import numpy as np
from src.fusion.decision_pipeline import DecisionPipeline
from src.iot.mqtt_client import MQTTClient
from src.iot.event_store import EventStore

class Gateway:
    """
    Simulates the central IoT Gateway that receives telemetry from edge nodes, 
    routes data, performs temporal/spatial transformations, executes model inference, 
    persists events in SQLite, and publishes final fused decision states.
    """
    def __init__(self, workspace_dir=None, use_mock=True):
        if workspace_dir is None:
            workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.workspace_dir = workspace_dir
        self.registry_path = os.path.join(workspace_dir, "config", "device_registry.json")
        self.mapping_path = os.path.join(workspace_dir, "config", "sensor_feature_mapping.json")

        self.device_registry = self._load_json(self.registry_path)
        self.sensor_mapping = self._load_json(self.mapping_path)

        # Inits
        self.pipeline = DecisionPipeline(workspace_dir)
        self.event_store = EventStore()
        
        self.client = MQTTClient(client_id="CENTRAL_GATEWAY", use_mock=use_mock)
        self.client.set_on_message(self.on_message_received)

        self.processed_count = 0
        self.fusion_failures = []

    def _load_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def resolve_us_region(self, lat: float, lon: float) -> str:
        """
        Deterministic geographic mapping of latitude/longitude to US census regions
        (west, midwest, south, northeast) as expected by the CAML model.
        """
        if lat is None or lon is None:
            return 'south'  # Safe default fallback
            
        # West region: generally longitude <= -114.0
        if lon <= -114.0:
            return 'west'
        
        # Northeast region: longitude >= -80.0 and latitude >= 38.0
        if lon >= -80.0 and lat >= 38.0:
            return 'northeast'
            
        # Midwest region: longitude between -105.0 and -80.0, latitude >= 36.5
        if -105.0 <= lon < -80.0 and lat >= 36.5:
            return 'midwest'
            
        # South region: fallback for everything else in the southern/southeastern US
        return 'south'

    def resolve_state_id(self, lat: float, lon: float) -> str:
        """
        Deterministic geographic mapping of latitude/longitude to state abbreviation
        (e.g., FL, TX) for the HABSOS model.
        """
        if lat is None or lon is None:
            return 'FL'
        # Simple bounding box: Texas is generally west of -93.5 longitude in the Gulf region
        if lon <= -93.5:
            return 'TX'
        return 'FL'

    def connect(self):
        self.client.connect()
        # Subscribe to all telemetry and decision publications
        self.client.subscribe("aquatic/+/telemetry")
        self.client.subscribe("aquatic/+/decision")

    def disconnect(self):
        self.client.disconnect()

    def on_message_received(self, topic, payload):
        """Callback when telemetry message is received via MQTT."""
        if not topic.endswith("/telemetry"):
            return

        self.processed_count += 1
        device_id = payload.get("device_id")

        try:
            # 1. Validation steps
            is_valid, err_msg = self.validate_telemetry_payload(payload)
            if not is_valid:
                self.event_store.log_error(datetime.datetime.now().isoformat(), device_id or "UNKNOWN", f"Validation Error: {err_msg}")
                self.event_store.log_validation(payload.get("timestamp") or datetime.datetime.now().isoformat(), device_id or "UNKNOWN", False, [err_msg], "FAULT")
                return

            self.event_store.log_validation(payload["timestamp"], device_id, True, [], payload["device_health"]["sensor_status"])
            
            # Log raw telemetry
            self.event_store.log_telemetry(payload)

            # Check for local edge validation sensor fault bypass
            if payload["device_health"]["sensor_status"] == "FAULT":
                decision = {
                    "timestamp": payload["timestamp"],
                    "device_id": device_id,
                    "ml_evidence": {
                        "predicted_class": "UNAVAILABLE",
                        "confidence": 0.0,
                        "dangerous_class": False,
                        "model_id": "UNAVAILABLE"
                    },
                    "ais_evidence": {
                        "is_anomaly": True,
                        "anomaly_score": 1.0,
                        "matched_detector_count": 0,
                        "nearest_detector_distance": 0.0,
                        "ais_model_id": "UNAVAILABLE"
                    },
                    "fusion": {
                        "final_state": "SENSOR_FAULT",
                        "reason_code": "SENSOR_FAULT_BYPASS",
                        "reasoning": "Telemetry flagged with sensor fault status. Model inference bypassed.",
                        "confidence_band": "LOW"
                    },
                    "system_metadata": {
                        "fusion_version": "1.0.0"
                    }
                }
            else:
                # 2. Extract and transform features
                dataset_route = payload["dataset_route"]
                X_df = self.transform_telemetry_to_features(payload)

                # 3. Execute model pipeline
                decision = self.pipeline.run_pipeline(dataset_route, X_df, sensors=payload.get("sensors"))

                # Add timestamp and device metadata to decision
                decision["timestamp"] = payload["timestamp"]
                decision["device_id"] = device_id

            # 4. Persistence
            self.event_store.log_decision(decision)

            # 5. Publish decision back to broker
            decision_topic = f"aquatic/{device_id}/decision"
            self.client.publish(decision_topic, decision)

            # 6. Publish command if critical
            if decision["fusion"]["final_state"] == "CRITICAL":
                cmd_topic = f"aquatic/{device_id}/command"
                cmd_payload = {
                    "command": "ACTIVATE_BUZZER",
                    "device_id": device_id
                }
                self.client.publish(cmd_topic, cmd_payload)
                self.event_store.log_command(datetime.datetime.now().isoformat(), device_id, "ACTIVATE_BUZZER", cmd_payload, "SENT")

        except Exception as e:
            err_msg = f"Gateway Pipeline Crash: {e}"
            self.fusion_failures.append(err_msg)
            self.event_store.log_error(datetime.datetime.now().isoformat(), device_id or "UNKNOWN", err_msg)

    def validate_telemetry_payload(self, p):
        """Validates payload structure, schema, device ID, and timestamps."""
        if not isinstance(p, dict):
            return False, "Payload is not a JSON object."
        
        required_keys = ["schema_version", "device_id", "timestamp", "dataset_route", "location", "sensors", "device_health"]
        for k in required_keys:
            if k not in p:
                return False, f"Missing required telemetry key: {k}"

        device_id = p["device_id"]
        if device_id not in self.device_registry["devices"]:
            return False, f"Unauthorized or unknown device ID: {device_id}"

        # Verify route matches registry
        device_profile = self.device_registry["devices"][device_id]
        if p["dataset_route"] != device_profile["dataset_route"]:
            return False, f"Route mismatch: telemetry={p['dataset_route']}, registry={device_profile['dataset_route']}"

        # Validate timestamp
        try:
            datetime.datetime.fromisoformat(p["timestamp"])
        except ValueError:
            return False, f"Invalid ISO timestamp format: {p['timestamp']}"

        if "provenance_timestamp" in p and p["provenance_timestamp"] is not None:
            try:
                datetime.datetime.fromisoformat(p["provenance_timestamp"])
            except ValueError:
                return False, f"Invalid ISO provenance timestamp format: {p['provenance_timestamp']}"

        return True, ""

    def transform_telemetry_to_features(self, p):
        """Converts sensor telemetry into exact model-compatible feature DataFrame."""
        device_id = p["device_id"]
        device_profile = self.device_registry["devices"][device_id]
        dataset_route = p["dataset_route"]

        # Parse timestamp variables
        ts = p.get("provenance_timestamp") or p["timestamp"]
        dt = datetime.datetime.fromisoformat(ts)
        year = dt.year
        month = dt.month
        day_of_year = dt.timetuple().tm_yday

        # Cyclic conversions
        month_sin = np.sin(2 * np.pi * month / 12.0)
        month_cos = np.cos(2 * np.pi * month / 12.0)
        day_sin = np.sin(2 * np.pi * day_of_year / 365.25)
        day_cos = np.cos(2 * np.pi * day_of_year / 365.25)

        # Standardize Season representation
        if month in [12, 1, 2]:
            season = "Winter"
        elif month in [3, 4, 5]:
            season = "Spring"
        elif month in [6, 7, 8]:
            season = "Summer"
        else:
            season = "Autumn"

        # Construct specific feature structures
        if dataset_route == "caml":
            # Expected: ['lat', 'lon', 'distance_to_water_m', 'region', 'Season', 'Year', 'Month_sin', 'Month_cos', 'DayOfYear_sin', 'DayOfYear_cos']
            # Try to get distance to water from telemetry sensor if not null, else registry default (120.0)
            dist = p["sensors"].get("distance_to_water_m")
            if dist is None or not np.isfinite(dist):
                dist = 120.0 # Default registry constant
            
            features = {
                'lat': p["location"]["latitude"],
                'lon': p["location"]["longitude"],
                'distance_to_water_m': dist,
                'region': self.resolve_us_region(p["location"]["latitude"], p["location"]["longitude"]),
                'Season': season,
                'Year': year,
                'Month_sin': month_sin,
                'Month_cos': month_cos,
                'DayOfYear_sin': day_sin,
                'DayOfYear_cos': day_cos
            }
        else: # habsos
            # Expected: ['LATITUDE', 'LONGITUDE', 'SAMPLE_DEPTH', 'SALINITY', 'WATER_TEMP', 'STATE_ID', 'Season', 'Year', 'Month', 'Month_sin', 'Month_cos', 'DayOfYear_sin', 'DayOfYear_cos']
            depth = p["sensors"].get("sample_depth")
            if depth is None or not np.isfinite(depth):
                depth = 1.0 # default surface depth

            features = {
                'LATITUDE': p["location"]["latitude"],
                'LONGITUDE': p["location"]["longitude"],
                'SAMPLE_DEPTH': depth,
                'SALINITY': p["sensors"]["salinity_ppt"] if p["sensors"]["salinity_ppt"] is not None else 35.0,
                'WATER_TEMP': p["sensors"]["temperature_c"] if p["sensors"]["temperature_c"] is not None else 24.0,
                'STATE_ID': self.resolve_state_id(p["location"]["latitude"], p["location"]["longitude"]),
                'Season': season,
                'Year': year,
                'Month': float(month),
                'Month_sin': month_sin,
                'Month_cos': month_cos,
                'DayOfYear_sin': day_sin,
                'DayOfYear_cos': day_cos
            }

        return pd.DataFrame([features])
