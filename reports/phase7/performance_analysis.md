# Performance and Latency Analysis Report

This report summarizes processing latency measured across various software steps of the virtual IoT pipeline.

| Step / Pipeline Phase | Mean Latency | Median Latency | p95 Latency | Maximum Latency |
|:---|:---|:---|:---|:---|
| **sensor_sim** | 0.41 ms | 0.05 ms | 2.00 ms | 3.30 ms |
| **edge_val** | 0.03 ms | 0.02 ms | 0.07 ms | 0.10 ms |
| **mqtt_trans** | 0.00 ms | 0.00 ms | 0.00 ms | 0.00 ms |
| **gateway_proc** | 184.74 ms | 53.36 ms | 845.94 ms | 1371.66 ms |
| **ml_inf** | 174.76 ms | 43.75 ms | 832.88 ms | 1355.77 ms |
| **ais_inf** | 2.05 ms | 1.37 ms | 4.53 ms | 5.51 ms |
| **fusion** | 0.02 ms | 0.01 ms | 0.06 ms | 0.09 ms |
| **end_to_end** | 187.08 ms | 54.77 ms | 850.93 ms | 1378.86 ms |

---

## Performance Discussion
- **Edge validation latency:** Extremely low (sub-millisecond) because validations consist of simple range boundary and history checks.
- **Model inference latency:** Supervised ML inference and unsupervised negative selection algorithm executions take the majority of processing time (~1-10 ms depending on model size and dimensions).
- **Fusion layer execution:** Extremely fast rule-based lookup, completing in sub-millisecond ranges.
