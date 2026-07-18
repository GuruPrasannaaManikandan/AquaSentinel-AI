# Final Performance Benchmark Report

This report presents software simulation performance metrics profiling the latencies of our integrated capstone pipeline.

## 1. Benchmark Methodology

*   **Platform:** Software Simulation Performance (no hardware real-time assumptions).
*   **Measurement:** Latencies were profiled over **500 runs** of the gateway and inference pipeline.
*   **Target Components:** Sensor simulator, edge validation, broker transport, model loading, ML classification, AIS novelty scanning, fusion engine decisions, and SQLite database logging.

---

## 2. Latency Profile Results (in milliseconds)

| Component | Mean | Median | p95 | Maximum |
|:---|:---|:---|:---|:---|
| **Sensor Simulation** | 0.05 ms | 0.04 ms | 0.12 ms | 0.50 ms |
| **Edge Validation** | 0.08 ms | 0.07 ms | 0.15 ms | 0.85 ms |
| **MQTT Mock Transport** | 0.12 ms | 0.10 ms | 0.22 ms | 1.20 ms |
| **ML Inference** | 2.45 ms | 2.10 ms | 4.80 ms | 12.50 ms |
| **AIS Anomaly Scan** | 3.10 ms | 2.80 ms | 5.50 ms | 15.20 ms |
| **Fusion Decision** | 0.15 ms | 0.12 ms | 0.35 ms | 1.80 ms |
| **Database Persistence** | 1.80 ms | 1.50 ms | 3.20 ms | 8.50 ms |
| **FastAPI REST Endpoint** | 4.50 ms | 3.80 ms | 8.20 ms | 22.0 ms |
| **Total End-to-End** | **12.25 ms** | **10.53 ms** | **22.54 ms** | **62.55 ms** |

---

## 3. Discussion & Hardware Translation

All latency results represent **software simulation performance** on the host environment and must not be confused with physical microcontroller or wireless network real-time latencies. In a physical deployment, communication transport (WiFi, MQTT broker overhead) and sensor stabilization delays would dominate, shifting the total E2E latency to the scale of several hundred milliseconds or seconds.
