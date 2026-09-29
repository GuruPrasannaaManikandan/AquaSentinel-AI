import time

print("Tracing dashboard/app.py execution step by step...")
import requests

API_URL = "http://localhost:8000"

def fetch_json(endpoint, method="GET", data=None):
    t0 = time.time()
    try:
        if method == "GET":
            r = requests.get(f"{API_URL}{endpoint}", timeout=3.0)
        else:
            r = requests.post(f"{API_URL}{endpoint}", json=data, timeout=3.0)
        dt = time.time() - t0
        print(f"  fetch_json({endpoint}) -> {r.status_code} in {dt:.3f}s")
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  fetch_json({endpoint}) -> ERROR {e}")
    return None

print("1. Fetching health...")
health = fetch_json("/health")
print("2. Fetching devices...")
devices = fetch_json("/devices") or []
print("3. Fetching system status...")
stats = fetch_json("/system/status")
print("4. Fetching simulation scenarios...")
active_scenarios = fetch_json("/simulation/scenarios")
selected_id = "AQUA_FRESH_001"
print("5. Fetching latest...")
latest_data = fetch_json(f"/devices/{selected_id}/latest")
print("6. Fetching intelligence...")
intel_data = fetch_json(f"/devices/{selected_id}/intelligence")
print("7. Fetching multimodal...")
multimodal_info = fetch_json(f"/devices/{selected_id}/multimodal")
print("8. Fetching response...")
v8_response_info = fetch_json(f"/devices/{selected_id}/response")
print("9. Fetching risk-trend...")
v8_trend_info = fetch_json(f"/devices/{selected_id}/risk-trend")
print("10. Fetching reliability...")
reliability_metrics = fetch_json("/system/reliability")

# Now check tabs 4, 5, 6, 7 in dashboard/app.py for any additional fetch_json calls!
with open("dashboard/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("\nSearching for other fetch_json calls in app.py:")
for idx, line in enumerate(lines):
    if "fetch_json" in line and not line.strip().startswith("def fetch_json"):
        print(f"Line {idx+1}: {line.strip()}")
