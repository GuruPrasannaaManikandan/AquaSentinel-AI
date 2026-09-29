import time
import requests

API_URL = "http://127.0.0.1:8000"
endpoints = [
    "/health",
    "/devices",
    "/system/status",
    "/simulation/scenarios",
    "/devices/AQUA_FRESH_001/latest",
    "/devices/AQUA_FRESH_001/intelligence",
    "/devices/AQUA_FRESH_001/multimodal",
    "/devices/AQUA_FRESH_001/response",
    "/devices/AQUA_FRESH_001/risk-trend",
    "/system/reliability",
    "/devices/AQUA_FRESH_001/telemetry?limit=100",
    "/alerts?acknowledged=false&limit=25",
    "/devices/AQUA_FRESH_001/decisions?limit=25"
]

print("=== FASTAPI ENDPOINT PERFORMANCE PROFILE (AFTER OPTIMIZATION) ===")
total_time = 0.0
total_bytes = 0
for ep in endpoints:
    t0 = time.perf_counter()
    try:
        r = requests.get(f"{API_URL}{ep}", timeout=5.0)
        dt = (time.perf_counter() - t0) * 1000.0
        total_time += dt
        size = len(r.content)
        total_bytes += size
        print(f"[{r.status_code}] {ep:<45} -> {dt:6.2f} ms ({size:6d} bytes)")
    except Exception as e:
        print(f"[ERR] {ep:<45} -> {e}")

print(f"\nTotal REST Latency for 13 calls: {total_time:.2f} ms")
print(f"Total Payload Size: {total_bytes / 1024:.2f} KB ({total_bytes} bytes)")
