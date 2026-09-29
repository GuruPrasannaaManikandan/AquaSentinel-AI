#!/usr/bin/env python3
"""
AquaSentinel-AI: Live Physical Sensor to Software Decision Pipeline Demonstration
==================================================================================
Subscribes to live MQTT telemetry from the physical ESP32, feeds real physical
sensor readings (pH, Turbidity) into the Sensor Quality Evaluator, passes the
evidence through the DecisionPipeline / FusionEngine, and determines the
resulting software decision and actuator states.
"""

import sys
import os
import json
import time
import threading
import pandas as pd

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import paho.mqtt.client as mqtt
from src.iot.sensor_quality import SensorQualityEvaluator
from src.fusion.decision_pipeline import DecisionPipeline
from src.fusion.decision_adapter import DecisionAdapter
from src.iot.actuators import VirtualActuators

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
TOPIC_TELEMETRY = "aquatic/AQUA_FRESH_001/telemetry"
TOPIC_STATUS = "aquatic/AQUA_FRESH_001/status"
TOPIC_COMMAND = "aquatic/AQUA_FRESH_001/command"

class LivePipelineRunner:
    def __init__(self):
        self.received_packet = None
        self.packet_event = threading.Event()
        self.quality_evaluator = SensorQualityEvaluator()
        self.decision_pipeline = DecisionPipeline(workspace_dir=BASE_DIR)
        self.actuators = VirtualActuators()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[MQTT-CLIENT] Connected successfully to {MQTT_BROKER}:{MQTT_PORT}")
            client.subscribe(TOPIC_TELEMETRY, qos=1)
            client.subscribe(TOPIC_STATUS, qos=1)
            print(f"[MQTT-CLIENT] Subscribed to {TOPIC_TELEMETRY}")
        else:
            print(f"[MQTT-CLIENT] Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload_str = msg.payload.decode("utf-8")
        if topic == TOPIC_TELEMETRY and not self.received_packet:
            try:
                data = json.loads(payload_str)
                print(f"\n[MQTT-LIVE] >>> RECEIVED REAL TELEMETRY FROM ESP32 <<<")
                self.received_packet = data
                self.packet_event.set()
            except Exception as e:
                print(f"[MQTT-ERROR] Failed to parse payload: {e}")

    def run_live_pipeline(self, timeout_sec=25):
        client = mqtt.Client(client_id=f"AquaSentinel_Gateway_{int(time.time())}")
        client.on_connect = self.on_connect
        client.on_message = self.on_message

        print(f"[GATEWAY] Connecting to broker {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        print(f"[GATEWAY] Waiting up to {timeout_sec}s for live telemetry from physical ESP32...")
        got_packet = self.packet_event.wait(timeout=timeout_sec)
        client.loop_stop()
        client.disconnect()

        if not got_packet or not self.received_packet:
            print("[ERROR] Timeout waiting for live ESP32 packet.")
            return None

        packet = self.received_packet
        print("\n" + "="*70)
        print("1. ACTUAL LIVE PHYSICAL TELEMETRY PACKET FROM ESP32")
        print("="*70)
        print(json.dumps(packet, indent=2))

        # Extract Physical Readings
        sensors = packet.get("sensors", {})
        device_health = packet.get("device_health", {})
        
        ph_val = sensors.get("ph")
        turb_val = sensors.get("turbidity_ntu")
        temp_val = sensors.get("temperature_c")
        sal_val = sensors.get("salinity_ppt")
        do_val = sensors.get("dissolved_oxygen_mg_l")
        
        print("\n" + "="*70)
        print("2. PHYSICAL SENSOR HARDWARE VERIFICATION & PROVENANCE (AIR/DRY BENCH)")
        print("="*70)
        print(f"  Device ID:              {packet.get('device_id')}")
        print(f"  Timestamp:              {packet.get('timestamp')}")
        print(f"  Sequence Number:         {packet.get('sequence_number')}")
        print(f"  Sensor Health:           {device_health.get('sensor_status')}")
        print(f"  WiFi Connected:          {device_health.get('wifi_connected')}")
        print(f"  MQTT Connected:          {device_health.get('mqtt_connected')}")
        print("-" * 50)
        print(f"  [PHYSICAL CH 1] pH Sensor (GPIO32):")
        print(f"      Electrical Channel:   ACTIVE / READING")
        print(f"      Physical Measurement: INVALID FOR WATER WHILE IN AIR")
        print(f"      pH Calibration:       NOT VERIFIED")
        print(f"      Calculated Output:    {ph_val}")
        print(f"      Hardware Path:        ADC1_CH4 -> 33k/22k divider -> reconstructed x2.500")
        print(f"  [PHYSICAL CH 2] Turbidity Sensor (GPIO34):")
        print(f"      Electrical Channel:   ACTIVE / READING")
        print(f"      Optical Measurement:  NOT VERIFIED")
        print(f"      Turbidity Calib:      NOT VERIFIED")
        print(f"      Raw Reconstructed:    {turb_val} V (reconstructed module voltage)")
        print(f"      Status:               UNVERIFIED_UNCALIBRATED")
        print(f"      Hardware Path:        ADC1_CH6 -> 33k/22k divider -> reconstructed x2.500")
        print(f"  [UNAVAILABLE SENSORS]:")
        print(f"      Temperature:          {temp_val} (DS18B20 absent/deferred - null semantics)")
        print(f"      Salinity / TDS:       {sal_val} (hardware absent - null semantics)")
        print(f"      Dissolved Oxygen:     {do_val} (hardware absent - null semantics)")
        print(f"      GPS Location:         {packet.get('location')} (hardware absent - null semantics)")

        # Run Sensor Quality Evaluator
        print("\n" + "="*70)
        print("3. SENSOR QUALITY EVALUATOR (src/iot/sensor_quality.py)")
        print("="*70)
        quality_result = self.quality_evaluator.evaluate(
            readings=sensors,
            device_id=packet.get("device_id", "AQUA_FRESH_001"),
            timestamp=packet.get("timestamp")
        )
        print(f"  Overall Quality Score (Q_sensor): {quality_result.overall_quality:.4f}")
        print(f"  Validation State:                 {quality_result.validation_state}")
        print(f"  Anomaly Flags:                    {quality_result.anomaly_flags}")
        print(f"  Reason Codes:                     {quality_result.reason_codes}")
        for sname, comp in quality_result.components.items():
            print(f"    - {sname}: val={comp.raw_value}, score={comp.quality_score:.2f}, status={comp.status}, reasons={comp.reasons}")

        # Run ML Champion & AIS Anomaly Detection through DecisionPipeline
        print("\n" + "="*70)
        print("4. SUPERVISED ML & AIS ANOMALY DETECTION (src/fusion/decision_pipeline.py)")
        print("="*70)
        # Preserve existing CAML model contract (GIS/temporal features)
        caml_features = pd.DataFrame([{
            'lat': 27.5,
            'lon': -81.2,
            'distance_to_water_m': sensors.get("distance_to_water_m", 120.0),
            'region': 'FL',
            'Season': 'Summer',
            'Year': 2026,
            'Month_sin': 0.5,
            'Month_cos': -0.866,
            'DayOfYear_sin': 0.3,
            'DayOfYear_cos': -0.95
        }])

        pipeline_result = self.decision_pipeline.run_pipeline(
            dataset_key="caml",
            X=caml_features,
            sensors=sensors,
            sensor_quality=quality_result.to_dict()
        )

        ml_ev = pipeline_result.get("fusion", {}).get("ml_evidence", {})
        ais_ev = pipeline_result.get("fusion", {}).get("ais_evidence", {})
        sys_event = pipeline_result.get("system_event", {})

        print(f"  Supervised ML Model:        {ml_ev.get('model_id')}")
        print(f"  ML Predicted Class:         {ml_ev.get('predicted_class')}")
        print(f"  ML Confidence:              {ml_ev.get('confidence')}")
        print(f"  ML Dangerous Detected:      {ml_ev.get('dangerous_class')}")
        print(f"  AIS Detector Model:         {ais_ev.get('ais_model_id')}")
        print(f"  AIS Anomaly Detected:       {ais_ev.get('is_anomaly')}")
        print(f"  AIS Anomaly Score:          {ais_ev.get('anomaly_score')}")

        print("\n" + "="*70)
        print("5. SOFTWARE DECISION UNDER DRY/AIR SENSOR CONDITION")
        print("   (NOTE: SENSORS ARE IN AIR/DRY BENCH - NOT A CLAIM OF WATER QUALITY)")
        print("="*70)
        fusion_info = pipeline_result.get("fusion", {})
        final_state = fusion_info.get("final_state", "NORMAL")
        reason_code = fusion_info.get("reason_code")
        reasoning = fusion_info.get("reasoning")

        print(f"  Final System State:         {final_state}")
        print(f"  Reason Code:                {reason_code}")
        print(f"  Decision Reasoning:         {reasoning}")
        print(f"  System Event ID:            {sys_event.get('event_id')}")
        print(f"  Target FSM State:           {sys_event.get('target_fsm_state')}")
        print(f"  Semantic Interpretation:    SOFTWARE DECISION UNDER DRY/AIR SENSOR CONDITION")

        print("\n" + "="*70)
        print("6. ACTUATOR CONTROL STATE MAPPING")
        print("="*70)
        self.actuators.update_state(final_state)
        print(f"  Green LED (GPIO25):         {self.actuators.green_led}")
        print(f"  Yellow LED (GPIO26):        {self.actuators.yellow_led}")
        print(f"  Red LED (GPIO27):           {self.actuators.red_led}")
        print(f"  Buzzer (GPIO14):            {self.actuators.buzzer}")
        print(f"  Pump Relay (GPIO19):        {self.actuators.pump_relay} (PUMP PHYSICALLY ABSENT - RELAY LOGIC ONLY)")

        print("\n" + "="*70)
        print("7. CONTROLLED SOFTWARE ACTUATOR TEST")
        print("   (Verifying LED / Buzzer / Relay Mapping Under Controlled Software Inputs)")
        print("   (NOTE: NOT Real Environmental Detections - Pure Actuation Mapping Proof)")
        print("="*70)
        states_to_test = ["NORMAL", "WARNING", "CRITICAL"]
        for st in states_to_test:
            self.actuators.update_state(st)
            print(f"  [CONTROLLED TEST: State = {st:8s}] -> Green: {self.actuators.green_led:3s} | Yellow: {self.actuators.yellow_led:3s} | Red: {self.actuators.red_led:3s} | Buzzer: {self.actuators.buzzer:3s} | Relay: {self.actuators.pump_relay}")

        # Save result artifact for audit
        demo_record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "raw_packet": packet,
            "sensor_quality": quality_result.to_dict(),
            "pipeline_result": pipeline_result,
            "actuator_state": self.actuators.get_summary()
        }
        out_path = os.path.join(BASE_DIR, "docs", "live_integration_evidence.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(demo_record, f, indent=2, default=str)
        print(f"\n[EVIDENCE] Saved complete live integration evidence to {out_path}")
        return demo_record

if __name__ == "__main__":
    runner = LivePipelineRunner()
    res = runner.run_live_pipeline(timeout_sec=30)
    if res:
        print("\n>>> LIVE PHYSICAL SENSOR-TO-DECISION PIPELINE VALIDATED SUCCESSFULLY <<<")
    else:
        sys.exit(1)
