import os
import sys
import time
import argparse
import tempfile
import sqlite3
from typing import Dict, Any

# Ensure project root is in sys.path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from src.iot.esp32_device import ESP32Device
from src.iot.gateway import Gateway
from src.iot.event_store import EventStore


def run_soak_test(cycles: int = 1000, db_path: str = None) -> Dict[str, Any]:
    """
    Executes a long-duration system soak test measuring throughput,
    latency percentiles (p50, p95, p99), error count, recovery count,
    database growth, and actuator command safety.
    """
    if db_path is None:
        fd, db_path = tempfile.mkstemp(suffix="_soak.db")
        os.close(fd)

    event_store = EventStore(db_path=db_path)
    device = ESP32Device(device_id="AQUA_FRESH_001", ecosystem_type="Freshwater", dataset_route="caml", use_mock=True)
    gateway = Gateway(workspace_dir=project_dir, use_mock=True)
    gateway.event_store = event_store

    device.boot()
    device.initialize_sensors()
    device.connect_network()
    gateway.connect()

    latencies = []
    error_count = 0
    recovery_count = 0
    degraded_count = 0
    false_escalation_count = 0
    actuator_cmd_count = 0

    initial_db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    start_time = time.perf_counter()

    for i in range(cycles):
        # Inject controlled patterns:
        # Every 100 cycles, trigger brief elevated risk then recover
        cycle_in_epoch = i % 100
        if 40 <= cycle_in_epoch <= 45:
            scenario = "KNOWN_BLOOM_RISK"
        elif cycle_in_epoch == 46:
            scenario = "NORMAL"  # recovery begins
        else:
            scenario = "NORMAL"

        cycle_start = time.perf_counter()
        try:
            telemetry = device.execute_one_complete_cycle(scenario=scenario)
            cycle_lat = (time.perf_counter() - cycle_start) * 1000.0
            latencies.append(cycle_lat)

            # Check decision
            dec = gateway.latest_decisions.get("AQUA_FRESH_001")
            if dec:
                pol = dec.get("autonomous_policy")
                if pol == "RECOVERY":
                    recovery_count += 1
                elif pol in ["INTERVENE", "EMERGENCY"]:
                    actuator_cmd_count += 1
                
                # Check for false escalation during normal cycles
                if scenario == "NORMAL" and cycle_in_epoch < 35 and pol in ["INTERVENE", "EMERGENCY"]:
                    false_escalation_count += 1
        except Exception as e:
            error_count += 1

    total_duration = time.perf_counter() - start_time
    final_db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    db_growth_bytes = final_db_size - initial_db_size

    throughput = cycles / max(0.001, total_duration)
    avg_latency = sum(latencies) / max(1, len(latencies))

    latencies_sorted = sorted(latencies) if latencies else [0.0]
    p50 = latencies_sorted[int(len(latencies_sorted) * 0.50)]
    p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)]
    p99 = latencies_sorted[int(len(latencies_sorted) * 0.99)]

    # Clean up
    device.comm.disconnect_mqtt()
    gateway.disconnect()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    return {
        "cycles_requested": cycles,
        "cycles_completed": len(latencies),
        "total_duration_sec": round(total_duration, 4),
        "throughput_cycles_sec": round(throughput, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "p50_latency_ms": round(p50, 2),
        "p95_latency_ms": round(p95, 2),
        "p99_latency_ms": round(p99, 2),
        "db_growth_bytes": db_growth_bytes,
        "error_count": error_count,
        "recovery_count": recovery_count,
        "false_escalation_count": false_escalation_count,
        "actuator_command_count": actuator_cmd_count,
        "degraded_mode_count": degraded_count,
        "success_rate_percent": round(((len(latencies) - error_count) / max(1, cycles)) * 100.0, 2)
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="V8 Long-Duration Soak Simulation Test")
    parser.add_argument("--cycles", type=int, default=1000, help="Number of soak test cycles (default: 1000)")
    args = parser.parse_args()

    print(f"==================================================")
    print(f"STARTING V8 LONG-DURATION SOAK TEST ({args.cycles} CYCLES)")
    print(f"==================================================")

    res = run_soak_test(cycles=args.cycles)

    print(f"Completed {res['cycles_completed']}/{res['cycles_requested']} cycles in {res['total_duration_sec']}s")
    print(f"Throughput: {res['throughput_cycles_sec']} cycles/sec")
    print(f"Latency: avg={res['avg_latency_ms']}ms, p50={res['p50_latency_ms']}ms, p95={res['p95_latency_ms']}ms, p99={res['p99_latency_ms']}ms")
    print(f"Errors: {res['error_count']}, False Escalations: {res['false_escalation_count']}")
    print(f"Actuator Interventions: {res['actuator_command_count']}, Recoveries: {res['recovery_count']}")
    print(f"DB Growth: {res['db_growth_bytes']} bytes")
    print(f"Success Rate: {res['success_rate_percent']}%")
    print(f"==================================================")
