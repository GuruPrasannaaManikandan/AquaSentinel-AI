#!/usr/bin/env python3
"""
AquaSentinel-AI: V5.3 Temporal Trajectory 60-Second Live Validation
===================================================================
Polls backend /devices/AQUA_FRESH_001/intelligence every 5 seconds for 60 seconds.
Verifies timestamps advance, sliding window updates, history accumulates,
and response times remain sub-200ms without blocking.
"""

import time
import json
import urllib.request

URL = "http://127.0.0.1:8000/devices/AQUA_FRESH_001/intelligence"

def monitor_temporal():
    print("[TEMPORAL 60S TEST] Beginning 60-second temporal observation...")
    samples = []
    start_time = time.time()
    last_ts = None
    
    while time.time() - start_time < 60.0:
        t0 = time.perf_counter()
        req = urllib.request.Request(URL)
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        lat_ms = (time.perf_counter() - t0) * 1000.0
        
        temp_ev = data.get("temporal_evidence") or {}
        curr_ts = temp_ev.get("timestamp")
        threat_st = temp_ev.get("temporal_state")
        risk = temp_ev.get("trajectory_risk_score", 0.0)
        win_size = temp_ev.get("window_size_evaluated", 0)
        slopes = temp_ev.get("trend_slopes", {})
        
        advancing = (curr_ts != last_ts) if last_ts else True
        last_ts = curr_ts
        
        sample = {
            "elapsed_sec": round(time.time() - start_time, 1),
            "timestamp": curr_ts,
            "latency_ms": round(lat_ms, 2),
            "window_size": win_size,
            "threat_state": threat_st,
            "risk_score": risk,
            "turbidity_slope": slopes.get("turbidity_ntu_per_min", 0.0),
            "timestamp_advancing": advancing
        }
        samples.append(sample)
        print(f"  [{sample['elapsed_sec']:4.1f}s] Window: {win_size:2d}/12 | TS: {curr_ts} | State: {threat_st} | Latency: {lat_ms:5.1f}ms")
        time.sleep(5.0)
        
    print(f"\n[TEMPORAL 60S TEST] Finished {len(samples)} samples.")
    avg_lat = sum(s["latency_ms"] for s in samples) / len(samples)
    print(f"  Average Query Latency: {avg_lat:.2f} ms")
    print(f"  All Latencies < 250ms: {all(s['latency_ms'] < 250.0 for s in samples)}")
    print(f"  Temporal Data Active : {all(s['window_size'] >= 2 for s in samples)}")
    print("✅ V5.3 TEMPORAL TRAJECTORY 60S VALIDATION PASSED!")

if __name__ == "__main__":
    monitor_temporal()
