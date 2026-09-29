import requests
import json
import time

API_URL = "http://127.0.0.1:8001"

def run_tests():
    print("=== 1. HEALTH & DEVICES ===")
    health = requests.get(f"{API_URL}/health").json()
    print("Health:", health)
    assert health.get("status") == "UP"
    devs = requests.get(f"{API_URL}/devices").json()
    print("Devices count:", len(devs))
    assert len(devs) >= 1

    print("\n=== 2. LATEST TELEMETRY ===")
    lat = requests.get(f"{API_URL}/devices/AQUA_FRESH_001/latest").json()
    tel = lat.get("telemetry", {})
    print("Device:", tel.get("device_id"))
    print("pH:", tel.get("ph"))
    print("Turbidity:", tel.get("turbidity_ntu"))
    print("Temperature:", tel.get("temperature_c"))
    print("DO:", tel.get("dissolved_oxygen_mg_l"))
    print("Salinity:", tel.get("salinity_ppt"))

    # Assertions for real physical hardware inventory
    assert tel.get("ph") is not None, "pH must be present from GPIO32"
    assert tel.get("turbidity_ntu") is not None, "Turbidity must be present from GPIO34"
    assert tel.get("temperature_c") is None, "Temperature must be None (DS18B20 physically disconnected)"
    assert tel.get("dissolved_oxygen_mg_l") is None, "DO must be None (Hardware not available)"
    assert tel.get("salinity_ppt") is None, "Salinity must be None (Hardware not available)"
    print("✓ Telemetry physical mapping verified!")

    print("\n=== 3. INTELLIGENCE & TREND SLOPES ===")
    intel = requests.get(f"{API_URL}/devices/AQUA_FRESH_001/intelligence").json()
    temp_ev = intel.get("temporal_evidence", {})
    slopes = temp_ev.get("trend_slopes", {})
    print("Trend Slopes:", json.dumps(slopes, indent=2))
    assert slopes.get("temperature_c_per_min") is None, "Temp slope must be None"
    assert slopes.get("dissolved_oxygen_mg_l_per_min") is None, "DO slope must be None"
    assert slopes.get("salinity_ppt_per_min") is None, "Salinity slope must be None"
    assert "turbidity_voltage_per_min" in slopes, "Turbidity voltage slope must be present"
    print("✓ Trend slope null & unit semantics verified!")

    print("\n=== 4. TEST ALL 8 COMMANDS ===")
    cmds = [
        ("REQUEST_READING", {}),
        ("SET_SAMPLING_INTERVAL", {"interval": 6}),
        ("ACTIVATE_BUZZER", {}),
        ("DEACTIVATE_BUZZER", {}),
        ("ACTIVATE_RELAY", {}),
        ("DEACTIVATE_RELAY", {}),
        ("PIN_DIAGNOSTICS", {}),
        ("RESTART_DEVICE", {})
    ]
    for cmd, payload in cmds:
        res = requests.post(f"{API_URL}/devices/AQUA_FRESH_001/command", json={"command": cmd, "payload": payload})
        data = res.json()
        status = data.get("execution_status")
        msg = data.get("message")
        print(f"Command {cmd:25s}: HTTP {res.status_code} -> {status} | {msg}")
        assert res.status_code == 200
        assert status == "COMMAND_COMPLETED"

    # Test invalid interval rejection
    bad_res = requests.post(f"{API_URL}/devices/AQUA_FRESH_001/command", json={"command": "SET_SAMPLING_INTERVAL", "payload": {"interval": 0}})
    print(f"Command SET_SAMPLING_INTERVAL (invalid=0): HTTP {bad_res.status_code} -> {bad_res.json().get('detail')}")
    assert bad_res.status_code == 400
    print("✓ All 8 commands and validation verified!")

    print("\n=== 5. CAMERA MANUAL CAPTURE WORKFLOW ===")
    cam_res = requests.post(f"{API_URL}/api/camera/capture?device_id=AQUA_FRESH_001")
    assert cam_res.status_code == 200
    cam = cam_res.json()
    print("Camera capture:", cam.get("capture_id"), "Frame #:", cam.get("frame_sequence"), "Sensor:", cam.get("sensor"))
    assert cam.get("success") == 1
    assert cam.get("sensor") == "GC2145"
    print("✓ Camera manual capture verified!")

    print("\n==========================================")
    print("✅ ALL HARDWARE & PIPELINE CRITERIA MET!")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
