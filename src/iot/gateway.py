import os
import json
import time
import datetime
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np
from src.fusion.decision_pipeline import DecisionPipeline
from src.iot.mqtt_client import MQTTClient
from src.iot.event_store import EventStore
from src.iot.sensor_quality import SensorQualityEvaluator

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
        self.quality_evaluator = SensorQualityEvaluator()
        from src.fusion.temporal_intelligence import TemporalEnvironmentalEngine
        self.temporal_engine = TemporalEnvironmentalEngine()
        from src.iot.historical_intelligence import HistoricalIntelligenceEngine
        self.historical_engine = HistoricalIntelligenceEngine()
        from src.fusion.risk_trajectory import RiskTrajectoryEngine
        self.risk_trajectory_engine = RiskTrajectoryEngine()
        from src.fusion.autonomous_response import AutonomousResponseEngine
        self.autonomous_response_engine = AutonomousResponseEngine()
        self.latest_risk_trend: Dict[str, Any] = {}
        self.latest_actuator_decision: Dict[str, Any] = {}
        self.latest_decisions: Dict[str, Any] = {}
        
        self.latest_visual_evidence: Dict[str, Any] = {}
        self._cv_preprocessor = None
        self._cv_model = None
        self._visual_detector = None
        self._optical_evaluator = None

        self.client = MQTTClient(client_id="CENTRAL_GATEWAY", use_mock=use_mock)
        self.client.set_on_message(self.on_message_received)

        self.processed_count = 0
        self.fusion_failures = []

    def _get_cv_components(self):
        """Lazily instantiates CV pipeline components for frame processing."""
        if self._cv_model is None:
            from src.cv.image_preprocessing import ImagePreprocessor
            from src.cv.cv_model import AquaticBloomCVModel
            from src.cv.visual_detection import VisualDetector
            from src.cv.optical_quality import OpticalQualityEvaluator
            self._cv_preprocessor = ImagePreprocessor()
            self._cv_model = AquaticBloomCVModel()
            self._cv_model.load()
            self._visual_detector = VisualDetector()
            self._optical_evaluator = OpticalQualityEvaluator()
        return self._cv_preprocessor, self._cv_model, self._visual_detector, self._optical_evaluator

    def process_camera_frame(
        self,
        device_id: str,
        frame_bytes_or_b64: Any,
        timestamp: Optional[str] = None,
        frame_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes an incoming camera frame (bytes, base64 string, or CameraFrame),
        evaluates optical quality Q_visual, runs MobileNetV3 inference, generates VisualEvidence,
        and caches it in self.latest_visual_evidence[device_id].
        """
        import base64
        from src.cv.camera_driver import CameraFrame
        ts = timestamp or datetime.datetime.now().isoformat()
        fid = frame_id or f"frame_{int(time.time() * 1000)}"

        if isinstance(frame_bytes_or_b64, CameraFrame):
            frame = frame_bytes_or_b64
        else:
            img_bytes = b""
            if isinstance(frame_bytes_or_b64, str):
                try:
                    img_bytes = base64.b64decode(frame_bytes_or_b64)
                except Exception:
                    img_bytes = b""
            elif isinstance(frame_bytes_or_b64, bytes):
                img_bytes = frame_bytes_or_b64

            is_valid = len(img_bytes) > 0 and (img_bytes.startswith(b"\xff\xd8") or img_bytes.startswith(b"\xff\xd8\xff"))
            frame = CameraFrame(
                frame_id=fid,
                timestamp=ts,
                width=224,
                height=224,
                channels=3,
                format="JPEG",
                image_bytes=img_bytes,
                quality_valid=is_valid,
                status="OK" if is_valid else "CORRUPTED"
            )

        preprocessor, model, detector, optical_evaluator = self._get_cv_components()

        # Optical quality
        opt_res = optical_evaluator.evaluate_image(frame.image_bytes, frame_id=frame.frame_id)

        # Preprocessing
        preproc_img = preprocessor.process(frame)

        # CV Model Predict
        cv_pred = model.predict(preproc_img)

        # Visual Detector evaluates prediction
        vis_ev = detector.evaluate_prediction(cv_pred, optical_quality=opt_res)
        vis_dict = vis_ev.to_dict()
        self.latest_visual_evidence[device_id] = vis_dict
        return vis_dict

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
        # Subscribe to all telemetry, decision, and camera publications
        self.client.subscribe("aquatic/+/telemetry")
        self.client.subscribe("aquatic/+/decision")
        self.client.subscribe("aquatic/+/camera/raw")

    def disconnect(self):
        self.client.disconnect()

    def on_message_received(self, topic, payload):
        """Callback when message is received via MQTT."""
        if "/camera/" in topic or topic.endswith("/camera/raw"):
            dev_id = payload.get("device_id") if isinstance(payload, dict) else topic.split("/")[1]
            b64_img = payload.get("image_b64", "") if isinstance(payload, dict) else ""
            ts = payload.get("timestamp") if isinstance(payload, dict) else None
            fid = payload.get("frame_id") if isinstance(payload, dict) else None
            self.process_camera_frame(dev_id, b64_img, timestamp=ts, frame_id=fid)
            return

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

            # V5.1 Sensor Quality Assessment
            sensor_quality = None
            if "sensors" in payload and payload["sensors"] is not None:
                q_res = self.quality_evaluator.evaluate(
                    payload["sensors"],
                    timestamp=payload.get("timestamp"),
                    device_id=device_id or "DEFAULT"
                )
                sensor_quality = q_res.to_dict()
                payload["sensor_quality"] = sensor_quality

            temporal_res = None
            hist_res = None
            vis_ev = self.latest_visual_evidence.get(device_id)

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
                        "fusion_version": "1.0.0",
                        "sensor_quality": sensor_quality
                    }
                }
            else:
                # 2. Extract and transform features
                dataset_route = payload["dataset_route"]
                X_df = self.transform_telemetry_to_features(payload)

                # V5.3 Temporal Environmental Trajectory Assessment
                temporal_res = None
                if "sensors" in payload and payload["sensors"] is not None:
                    q_s = sensor_quality.get("q_sensor", 1.0) if sensor_quality else 1.0
                    temporal_res = self.temporal_engine.evaluate_telemetry(
                        device_id or "DEFAULT",
                        payload["sensors"],
                        q_sensor=q_s
                    )

                # V5.5 / V7 Historical Digital Baseline Context
                hist_res = None
                if "sensors" in payload and payload["sensors"] is not None:
                    hist_res = self.historical_engine.update_and_evaluate(
                        device_id or "DEFAULT",
                        payload["sensors"]
                    )

                # 3. Execute model pipeline with multimodal visual & historical evidence
                vis_ev = self.latest_visual_evidence.get(device_id)
                decision = self.pipeline.run_pipeline(
                    dataset_route,
                    X_df,
                    sensors=payload.get("sensors"),
                    visual_evidence=vis_ev,
                    sensor_quality=sensor_quality,
                    temporal_evidence=temporal_res,
                    use_adaptive_ais=True,
                    historical_evidence=hist_res
                )

                # Add timestamp and device metadata to decision
                decision["timestamp"] = payload["timestamp"]
                decision["device_id"] = device_id
                if sensor_quality is not None and "sensor_quality" not in decision:
                    decision["sensor_quality"] = sensor_quality
                if temporal_res is not None and "temporal_evidence" not in decision:
                    decision["temporal_evidence"] = temporal_res.to_dict()
                if vis_ev is not None and "visual_evidence" not in decision:
                    decision["visual_evidence"] = vis_ev

            # V8 Risk Trajectory & Early-Warning Horizon
            trend_res = self.risk_trajectory_engine.evaluate_trajectory(
                device_id or "DEFAULT",
                decision,
                temporal_evidence=temporal_res.to_dict() if temporal_res else None,
                sensor_quality=sensor_quality,
                historical_evidence=hist_res
            )
            decision["risk_trend"] = trend_res.to_dict()
            self.latest_risk_trend[device_id] = trend_res.to_dict()

            # V8 Autonomous Response Policy & Safety Gate Interceptor
            policy_state, act_decision = self.autonomous_response_engine.evaluate_response(
                device_id or "DEFAULT",
                decision,
                trend_res,
                sensor_quality=sensor_quality,
                visual_evidence=vis_ev
            )
            decision["autonomous_policy"] = policy_state
            decision["actuator_decision"] = act_decision.to_dict()
            self.latest_actuator_decision[device_id] = act_decision.to_dict()
            self.latest_decisions[device_id] = decision

            # 4. Persistence
            self.event_store.log_decision(decision)
            if "multimodal_snapshot" in decision or "multimodal_intelligence" in decision:
                self.event_store.log_multimodal_event(decision)
            self.event_store.log_actuator_decision(act_decision)
            self.event_store.log_risk_trend_event(device_id or "DEFAULT", trend_res)

            # 5. Publish decision & intelligence back to broker
            decision_topic = f"aquatic/{device_id}/decision"
            self.client.publish(decision_topic, decision)

            # Publish multimodal event if available
            if "multimodal_intelligence" in decision:
                self.client.publish(f"aquatic/{device_id}/multimodal", decision["multimodal_intelligence"])

            # Publish V8 risk trend & response policy
            self.client.publish(f"aquatic/{device_id}/risk_trend", trend_res.to_dict())
            self.client.publish(f"aquatic/{device_id}/response", act_decision.to_dict())

            # 6. Execute Approved Actuator Commands via Safety Gate
            if act_decision.approved_action == "APPROVED" and act_decision.requested_action in ["ACTIVATE_BUZZER", "ACTIVATE_PUMP"]:
                cmd_topic = f"aquatic/{device_id}/command"
                cmd_payload = {
                    "command": act_decision.requested_action,
                    "device_id": device_id,
                    "command_id": act_decision.command_id
                }
                self.client.publish(cmd_topic, cmd_payload)
                self.event_store.log_command(datetime.datetime.now().isoformat(), device_id, act_decision.requested_action, cmd_payload, "SENT")
                self.event_store.update_actuator_execution_status(act_decision.command_id, "COMMAND_ISSUED")

            # Observability recording
            from src.utils.observability import observability_collector, CycleMetrics
            observability_collector.record_cycle(
                CycleMetrics(
                    cycle_id=self.processed_count,
                    timestamp=payload.get("timestamp", datetime.datetime.now().isoformat()),
                    device_id=device_id or "DEFAULT",
                    total_latency_ms=10.0,
                    status="SUCCESS",
                    safety_gate_blocked=(act_decision.approved_action == "BLOCKED"),
                    actuator_action=act_decision.approved_action
                )
            )

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
            
            lat = p["location"].get("latitude") if p.get("location") and p["location"].get("latitude") is not None else 27.5
            lon = p["location"].get("longitude") if p.get("location") and p["location"].get("longitude") is not None else -81.2

            features = {
                'lat': lat,
                'lon': lon,
                'distance_to_water_m': dist,
                'region': self.resolve_us_region(lat, lon),
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

            lat = p["location"].get("latitude") if p.get("location") and p["location"].get("latitude") is not None else 27.5
            lon = p["location"].get("longitude") if p.get("location") and p["location"].get("longitude") is not None else -82.5

            features = {
                'LATITUDE': lat,
                'LONGITUDE': lon,
                'SAMPLE_DEPTH': depth,
                'SALINITY': p["sensors"]["salinity_ppt"] if p["sensors"]["salinity_ppt"] is not None else 35.0,
                'WATER_TEMP': p["sensors"]["temperature_c"] if p["sensors"]["temperature_c"] is not None else 24.0,
                'STATE_ID': self.resolve_state_id(lat, lon),
                'Season': season,
                'Year': year,
                'Month': float(month),
                'Month_sin': month_sin,
                'Month_cos': month_cos,
                'DayOfYear_sin': day_sin,
                'DayOfYear_cos': day_cos
            }

        return pd.DataFrame([features])


IoTEdgeGateway = Gateway
