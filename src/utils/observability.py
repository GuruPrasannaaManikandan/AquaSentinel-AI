import time
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional

# Structured logger setup
logger = logging.getLogger("aquatic_observability")


@dataclass
class CycleMetrics:
    """Telemetry-to-actuation cycle metrics."""
    cycle_id: int
    timestamp: str
    device_id: str
    total_latency_ms: float
    validation_latency_ms: float = 0.0
    fusion_latency_ms: float = 0.0
    trend_latency_ms: float = 0.0
    response_latency_ms: float = 0.0
    persistence_latency_ms: float = 0.0
    status: str = "SUCCESS"  # "SUCCESS", "DEGRADED", "ERROR"
    safety_gate_blocked: bool = False
    actuator_action: str = "NO_ACTION"


class ObservabilityCollector:
    """
    Research-Grade Observability & Performance Metrics Collector.
    Tracks cycle throughput, latency percentiles (p50, p95, p99),
    error rates, false escalation counters, and safety gate interventions.
    """
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.cycle_records: List[CycleMetrics] = []
        self.total_cycles: int = 0
        self.successful_cycles: int = 0
        self.failed_cycles: int = 0
        self.degraded_cycles: int = 0
        self.safety_gate_blocks: int = 0
        self.actuator_commands_issued: int = 0
        self.start_time: float = time.time()

    def record_cycle(self, metric: CycleMetrics):
        self.total_cycles += 1
        if metric.status == "SUCCESS":
            self.successful_cycles += 1
        elif metric.status == "DEGRADED":
            self.degraded_cycles += 1
        else:
            self.failed_cycles += 1

        if metric.safety_gate_blocked:
            self.safety_gate_blocks += 1

        if metric.actuator_action not in ["NO_ACTION", "BLOCKED"]:
            self.actuator_commands_issued += 1

        if len(self.cycle_records) >= self.max_history:
            self.cycle_records.pop(0)
        self.cycle_records.append(metric)

    def get_summary_metrics(self) -> Dict[str, Any]:
        uptime_sec = max(0.001, time.time() - self.start_time)
        throughput = self.total_cycles / uptime_sec

        latencies = [c.total_latency_ms for c in self.cycle_records]
        if latencies:
            latencies_sorted = sorted(latencies)
            p50 = latencies_sorted[int(len(latencies_sorted) * 0.50)]
            p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)]
            p99 = latencies_sorted[int(len(latencies_sorted) * 0.99)]
            avg_lat = sum(latencies) / len(latencies)
        else:
            p50, p95, p99, avg_lat = 0.0, 0.0, 0.0, 0.0

        return {
            "total_cycles": self.total_cycles,
            "successful_cycles": self.successful_cycles,
            "failed_cycles": self.failed_cycles,
            "degraded_cycles": self.degraded_cycles,
            "safety_gate_blocks": self.safety_gate_blocks,
            "actuator_commands_issued": self.actuator_commands_issued,
            "uptime_seconds": round(uptime_sec, 2),
            "throughput_cycles_sec": round(throughput, 2),
            "latency_avg_ms": round(avg_lat, 2),
            "latency_p50_ms": round(p50, 2),
            "latency_p95_ms": round(p95, 2),
            "latency_p99_ms": round(p99, 2),
            "success_rate_percent": round((self.successful_cycles / max(1, self.total_cycles)) * 100.0, 2)
        }


# Global singleton instance
observability_collector = ObservabilityCollector()
