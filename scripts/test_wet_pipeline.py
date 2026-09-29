import json
import sys
import os
sys.path.insert(0, os.path.abspath("."))
from src.iot.sensor_quality import SensorQualityEvaluator
from src.fusion.decision_pipeline import DecisionPipeline
from src.iot.event_store import EventStore

def test_wet_pipeline():
    print("=" * 70)
    print("PHASE 11, 12, 13: GATEWAY, QUALITY ENGINE & DECISION PIPELINE ON WET DATA")
    print("=" * 70)
    
    # 1. Fetch latest telemetry event from SQLite EventStore
    store = EventStore("models/fusion/aquatic_events.db")
    latest_telemetry = store.get_latest_telemetry("AQUA_FRESH_001")
    latest_decision = store.get_latest_decision("AQUA_FRESH_001")
    
    print("\n--- 1. LATEST EVENT IN EVENT STORE ---")
    print("Telemetry Record:")
    print(f"  Event ID:      {latest_telemetry.get('id')}")
    print(f"  Timestamp:     {latest_telemetry.get('timestamp')}")
    print(f"  pH:            {latest_telemetry.get('ph')}")
    print(f"  Turbidity:     {latest_telemetry.get('turbidity_ntu')} V")
    print(f"  Temperature:   {latest_telemetry.get('temperature_c')}")
    print(f"  Salinity:      {latest_telemetry.get('salinity_ppt')}")
    print(f"  DO:            {latest_telemetry.get('dissolved_oxygen_mg_l')}")
    print(f"  Sensor Status: {latest_telemetry.get('sensor_status')}")
    print(f"  WiFi / MQTT:   {latest_telemetry.get('wifi_connected')} / {latest_telemetry.get('mqtt_connected')}")
    
    # 2. Evaluate with SensorQualityEvaluator
    print("\n--- 2. SENSOR QUALITY EVALUATION ---")
    evaluator = SensorQualityEvaluator()
    q_result = evaluator.evaluate(latest_telemetry)
    print(f"  Overall Q_sensor:     {q_result.overall_quality:.3f}")
    print(f"  Validation State:     {q_result.validation_state}")
    print(f"  Reason Codes:         {q_result.reason_codes}")
    print(f"  Anomaly Flags:        {q_result.anomaly_flags}")
    print("  Per-Sensor Components:")
    for sensor, comp in q_result.components.items():
        print(f"    - {sensor:15s}: raw={comp.raw_value} | score={comp.quality_score:.3f} | status={comp.status} | reasons={comp.reasons}")
        
    # 3. Decision Pipeline Evaluation
    print("\n--- 3. DECISION PIPELINE ON WET TELEMETRY ---")
    if latest_decision:
        print(f"  Decision ID:        {latest_decision.get('id')}")
        print(f"  Timestamp:          {latest_decision.get('timestamp')}")
        print(f"  ML Predicted Class: {latest_decision.get('ml_predicted_class')}")
        print(f"  ML Confidence:      {latest_decision.get('ml_confidence'):.4f}")
        print(f"  AIS Anomaly Score:  {latest_decision.get('ais_anomaly_score')}")
        print(f"  Final State:        {latest_decision.get('final_state')}")
        print(f"  Reason Code:        {latest_decision.get('reason_code')}")
        print(f"  Reasoning:          {latest_decision.get('reasoning')}")
        print(f"  Actuator Summary:   {latest_decision.get('actuator_summary')}")
    else:
        print("  No decision found in event store.")

    print("=" * 70)

if __name__ == "__main__":
    test_wet_pipeline()
