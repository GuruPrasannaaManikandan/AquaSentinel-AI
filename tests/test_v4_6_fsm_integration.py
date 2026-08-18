import io
import unittest
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw

from src.cv.camera_driver import CameraFrame, VirtualCameraDriver
from src.cv.image_preprocessing import ImagePreprocessor
from src.cv.cv_model import AquaticBloomCVModel
from src.cv.visual_detection import VisualDetector, VisualEvidence
from src.fusion.fusion_engine import FusionEngine
from src.fusion.decision_pipeline import DecisionPipeline
from src.fusion.decision_adapter import DecisionAdapter, SystemEvent
from src.iot.actuators import VirtualActuators

class TestV46FSMIntegration(unittest.TestCase):
    def setUp(self):
        self.adapter = DecisionAdapter(deduplication_window_sec=0.5)
        self.fusion_engine = FusionEngine()
        self.pipeline = DecisionPipeline()
        self.actuators = VirtualActuators()

        self.camera = VirtualCameraDriver(name="TEST_CAM_V46", resolution=(640, 480))
        self.camera.init()
        self.preprocessor = ImagePreprocessor(target_size=(224, 224), color_space="RGB", normalization_type="RESCALE")
        self.cv_model = AquaticBloomCVModel()
        self.cv_model.load()
        self.visual_detector = VisualDetector()

        self.mock_ml_normal = {
            "dataset": "caml",
            "predicted_class": 0,
            "class_probabilities": {0: 0.90, 1: 0.10},
            "confidence": 0.90,
            "dangerous_class": False,
            "model_id": "RandomForest-v1.0.0"
        }
        self.mock_ml_dangerous = {
            "dataset": "caml",
            "predicted_class": 4,
            "class_probabilities": {0: 0.10, 4: 0.90},
            "confidence": 0.90,
            "dangerous_class": True,
            "model_id": "RandomForest-v1.0.0"
        }
        self.mock_ais_normal = {
            "dataset": "caml",
            "is_anomaly": False,
            "anomaly_score": 0.10,
            "matched_detector_count": 5,
            "nearest_detector_distance": 0.05,
            "ais_model_id": "NSA-v1.0.0"
        }

        # Single row DataFrame for DecisionPipeline testing
        self.sample_df = pd.DataFrame([{
            'lat': 27.5,
            'lon': -81.2,
            'distance_to_water_m': 120.0,
            'region': 'south',
            'Season': 'Summer',
            'Year': 2026,
            'Month_sin': 0.0,
            'Month_cos': -1.0,
            'DayOfYear_sin': -0.8,
            'DayOfYear_cos': -0.5
        }])

    def test_01_normal_fused_evidence(self):
        fused = self.fusion_engine.fuse(self.mock_ml_normal, self.mock_ais_normal)
        evt = self.adapter.adapt(fused)
        self.assertEqual(evt.event_type, "SYSTEM_STATE_NORMAL")
        self.assertEqual(evt.target_fsm_state, "NORMAL")
        self.actuators.update_state(evt.target_fsm_state)
        self.assertEqual(self.actuators.green_led, "ON")
        self.assertEqual(self.actuators.pump_relay, "OFF")

    def test_02_warning_fused_evidence(self):
        vis_ev = VisualEvidence(
            frame_id="F01", timestamp="2026-08-17T22:00:00Z",
            predicted_visual_class="ALGAL_BLOOM", confidence=0.90,
            visual_state="BLOOM_EVIDENCE", risk_level="HIGH"
        )
        fused = self.fusion_engine.fuse(self.mock_ml_normal, self.mock_ais_normal, visual_evidence=vis_ev)
        evt = self.adapter.adapt(fused)
        self.assertEqual(evt.event_type, "SYSTEM_STATE_WARNING")
        self.assertEqual(evt.target_fsm_state, "WARNING")
        self.actuators.update_state(evt.target_fsm_state)
        self.assertEqual(self.actuators.yellow_led, "ON")
        self.assertEqual(self.actuators.pump_relay, "ON")

    def test_03_critical_fused_evidence(self):
        vis_ev = VisualEvidence(
            frame_id="F02", timestamp="2026-08-17T22:00:00Z",
            predicted_visual_class="ALGAL_BLOOM", confidence=0.95,
            visual_state="BLOOM_EVIDENCE", risk_level="HIGH"
        )
        fused = self.fusion_engine.fuse(self.mock_ml_dangerous, self.mock_ais_normal, visual_evidence=vis_ev)
        evt = self.adapter.adapt(fused)
        self.assertEqual(evt.event_type, "SYSTEM_STATE_CRITICAL")
        self.assertEqual(evt.target_fsm_state, "CRITICAL")
        self.actuators.update_state(evt.target_fsm_state)
        self.assertEqual(self.actuators.red_led, "ON")
        self.assertEqual(self.actuators.buzzer, "ON")
        self.assertEqual(self.actuators.pump_relay, "ON")

    def test_04_unknown_anomaly_fused_evidence(self):
        mock_ais_anom = self.mock_ais_normal.copy()
        mock_ais_anom["is_anomaly"] = True
        fused = self.fusion_engine.fuse(self.mock_ml_normal, mock_ais_anom)
        evt = self.adapter.adapt(fused)
        self.assertEqual(evt.target_fsm_state, "UNKNOWN_ANOMALY")
        self.actuators.update_state(evt.target_fsm_state)
        self.assertEqual(self.actuators.yellow_led, "ON")
        self.assertEqual(self.actuators.red_led, "ON")
        self.assertEqual(self.actuators.pump_relay, "OFF")

    def test_05_normal_to_warning_transition(self):
        self.actuators.update_state("NORMAL")
        self.assertEqual(self.actuators.green_led, "ON")
        self.actuators.update_state("WARNING")
        self.assertEqual(self.actuators.yellow_led, "ON")
        self.assertEqual(self.actuators.green_led, "OFF")

    def test_06_warning_to_critical_transition(self):
        self.actuators.update_state("WARNING")
        self.assertEqual(self.actuators.yellow_led, "ON")
        self.actuators.update_state("CRITICAL")
        self.assertEqual(self.actuators.red_led, "ON")
        self.assertEqual(self.actuators.buzzer, "ON")

    def test_07_critical_to_warning_transition(self):
        self.actuators.update_state("CRITICAL")
        self.assertEqual(self.actuators.buzzer, "ON")
        self.actuators.update_state("WARNING")
        self.assertEqual(self.actuators.buzzer, "OFF")
        self.assertEqual(self.actuators.yellow_led, "ON")

    def test_08_warning_to_normal_transition(self):
        self.actuators.update_state("WARNING")
        self.assertEqual(self.actuators.pump_relay, "ON")
        self.actuators.update_state("NORMAL")
        self.assertEqual(self.actuators.pump_relay, "OFF")
        self.assertEqual(self.actuators.green_led, "ON")

    def test_09_critical_to_normal_transition(self):
        self.actuators.update_state("CRITICAL")
        self.assertEqual(self.actuators.red_led, "ON")
        self.actuators.update_state("NORMAL")
        self.assertEqual(self.actuators.red_led, "OFF")
        self.assertEqual(self.actuators.green_led, "ON")

    def test_10_sensor_only_decision(self):
        fused = self.fusion_engine.fuse(self.mock_ml_normal, self.mock_ais_normal, visual_evidence=None)
        evt = self.adapter.adapt(fused)
        self.assertFalse(evt.multimodal)
        self.assertTrue(evt.sensor_contribution)
        self.assertFalse(evt.visual_contribution)

    def test_11_visual_decision_early_warning(self):
        vis_ev = VisualEvidence(
            frame_id="F11", timestamp="2026-08-17T22:00:00Z",
            predicted_visual_class="ALGAL_BLOOM", confidence=0.95,
            visual_state="BLOOM_EVIDENCE", risk_level="HIGH"
        )
        fused = self.fusion_engine.fuse(self.mock_ml_normal, self.mock_ais_normal, visual_evidence=vis_ev)
        evt = self.adapter.adapt(fused)
        self.assertTrue(evt.multimodal)
        self.assertTrue(evt.visual_contribution)
        self.assertEqual(evt.reason_code, "VISUAL_EARLY_WARNING")

    def test_12_camera_fault_handling(self):
        vis_fault = VisualEvidence(
            frame_id="F12", timestamp="2026-08-17T22:00:00Z",
            predicted_visual_class="UNCERTAIN", confidence=0.0,
            visual_state="CAMERA_FAULT", risk_level="UNKNOWN"
        )
        fused = self.fusion_engine.fuse(self.mock_ml_dangerous, self.mock_ais_normal, visual_evidence=vis_fault)
        evt = self.adapter.adapt(fused)
        self.assertEqual(evt.target_fsm_state, "WARNING")
        self.assertEqual(evt.reason_code, "VISUAL_CAMERA_FAULT")

    def test_13_multimodal_fusion_conflict(self):
        vis_ev = VisualEvidence(
            frame_id="F13", timestamp="2026-08-17T22:00:00Z",
            predicted_visual_class="ALGAL_BLOOM", confidence=0.95,
            visual_state="BLOOM_EVIDENCE", risk_level="HIGH"
        )
        fused = self.fusion_engine.fuse(self.mock_ml_normal, self.mock_ais_normal, visual_evidence=vis_ev)
        evt = self.adapter.adapt(fused)
        self.assertTrue(evt.conflict_detected)

    def test_14_stale_evidence_handling(self):
        vis_stale = VisualEvidence(
            frame_id="F14", timestamp="2020-01-01T00:00:00Z",
            predicted_visual_class="ALGAL_BLOOM", confidence=0.95,
            visual_state="CAMERA_FAULT", risk_level="UNKNOWN"
        )
        fused = self.fusion_engine.fuse(self.mock_ml_normal, self.mock_ais_normal, visual_evidence=vis_stale)
        evt = self.adapter.adapt(fused)
        self.assertEqual(evt.target_fsm_state, "NORMAL")

    def test_15_duplicate_event_deduplication(self):
        fused = self.fusion_engine.fuse(self.mock_ml_normal, self.mock_ais_normal)
        evt1 = self.adapter.adapt(fused)
        is_dup1 = self.adapter.is_duplicate(evt1)
        self.assertFalse(is_dup1)

        evt2 = self.adapter.adapt(fused)
        is_dup2 = self.adapter.is_duplicate(evt2)
        self.assertTrue(is_dup2)

    def test_16_invalid_fused_evidence_exception(self):
        with self.assertRaises(TypeError):
            self.adapter.adapt("INVALID_INPUT_STRING")

    def test_17_full_hardware_end_to_end_path(self):
        """Physical JPEG -> Preprocessor -> MobileNetV3 -> VisualDetector -> FusionEngine -> Adapter -> Actuators."""
        img = Image.new("RGB", (1920, 1080), color=(15, 170, 35))
        draw = ImageDraw.Draw(img)
        for _ in range(30):
            x0 = np.random.randint(0, 1500)
            y0 = np.random.randint(0, 800)
            x1 = x0 + np.random.randint(100, 400)
            y1 = y0 + np.random.randint(100, 300)
            draw.ellipse([x0, y0, x1, y1], fill=(5, 220, 20))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        frame = CameraFrame(
            frame_id="E2E_001", timestamp="2026-08-17T22:15:00Z",
            width=1920, height=1080, channels=3, format="JPEG",
            image_bytes=buf.getvalue(), quality_valid=True, status="OK"
        )

        preproc = self.preprocessor.process(frame)
        pred = self.cv_model.predict(preproc)
        vis_ev = self.visual_detector.evaluate_prediction(pred)

        fused = self.fusion_engine.fuse(self.mock_ml_dangerous, self.mock_ais_normal, visual_evidence=vis_ev)
        evt = self.adapter.adapt(fused)

        self.assertEqual(evt.target_fsm_state, "CRITICAL")
        self.actuators.update_state(evt.target_fsm_state)
        self.assertEqual(self.actuators.red_led, "ON")
        self.assertEqual(self.actuators.buzzer, "ON")

    def test_18_actuator_invocation_through_virtual_actuators(self):
        self.actuators.update_state("CRITICAL")
        summary = self.actuators.get_summary()
        self.assertIn("LEDs(G=OFF, Y=OFF, R=ON)", summary)
        self.assertIn("Buzzer=ON", summary)
        self.assertIn("Pump=ON", summary)

    def test_19_decision_pipeline_invokes_decision_adapter_runtime_wiring(self):
        """Verifies that DecisionPipeline.run_pipeline() automatically invokes DecisionAdapter and embeds system_event."""
        result = self.pipeline.run_pipeline("caml", self.sample_df)
        
        self.assertIn("system_event", result)
        sys_evt = result["system_event"]
        self.assertIn("event_id", sys_evt)
        self.assertIn("event_type", sys_evt)
        self.assertIn("target_fsm_state", sys_evt)
        self.assertEqual(sys_evt["target_fsm_state"], result["fusion"]["final_state"])

    def test_20_decision_pipeline_e2e_with_trained_mobilenetv3_model(self):
        """Verifies full DecisionPipeline.run_pipeline execution with visual evidence from trained MobileNetV3 PyTorch model."""
        img = Image.new("RGB", (1920, 1080), color=(15, 170, 35))
        draw = ImageDraw.Draw(img)
        for _ in range(30):
            x0 = np.random.randint(0, 1500)
            y0 = np.random.randint(0, 800)
            x1 = x0 + np.random.randint(100, 400)
            y1 = y0 + np.random.randint(100, 300)
            draw.ellipse([x0, y0, x1, y1], fill=(5, 220, 20))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        frame = CameraFrame(
            frame_id="E2E_PIPE_001", timestamp="2026-08-17T22:30:00Z",
            width=1920, height=1080, channels=3, format="JPEG",
            image_bytes=buf.getvalue(), quality_valid=True, status="OK"
        )

        preproc = self.preprocessor.process(frame)
        pred = self.cv_model.predict(preproc)
        vis_ev = self.visual_detector.evaluate_prediction(pred)

        # Run full pipeline with visual_evidence
        result = self.pipeline.run_pipeline("caml", self.sample_df, visual_evidence=vis_ev)

        self.assertIn("system_event", result)
        sys_evt = result["system_event"]
        self.assertTrue(sys_evt["multimodal"])
        self.assertTrue(sys_evt["visual_contribution"])
        self.assertIn(sys_evt["target_fsm_state"], ["WARNING", "CRITICAL"])

if __name__ == "__main__":
    unittest.main()
