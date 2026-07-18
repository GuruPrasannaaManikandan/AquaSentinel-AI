# Final Release Checklist

This document presents the final verification status for all capstone deliverables.

| Category | Verification Criteria | Status | Notes |
|:---|:---|:---|:---|
| **Datasets** | Raw validation files exist; test sets quarantined. | **PASS** | `caml_test.csv` and `habsos_test.csv` are closed and unused. |
| **Preprocessing** | Feature scales and cyclic dimensions match. | **PASS** | Cyclic mapping converts dates to 2D coordinates. |
| **ML Models** | Phase 3 champions deployed; manifest lock active. | **PASS** | E2E loops load RF and LR models correctly. |
| **AIS Models** | Negative selection algorithm active. | **PASS** | CAML and HABSOS NSA weights and detector matrices verified. |
| **Fusion Engine** | Gateway logic resolves ML + AIS inputs. | **PASS** | Uses policies configured in `fusion_policy.json`. |
| **IoT Simulators** | ESP32 state machines run on mock MQTT broker. | **PASS** | Triggers state transitions and handles command channels. |
| **Gateway Router** | Telemetry converted and routed cleanly. | **PASS** | Rejects unauthorized client connections. |
| **Actuators** | Relays and LED indicators map correctly. | **PASS** | Buzzer overrides trigger in real-time. |
| **Persistence** | SQLite logging of E2E telemetry and decisions. | **PASS** | Logged persistently to `aquatic_events.db`. |
| **Backend API** | FastAPI starts, exposing REST and WebSockets. | **PASS** | WebSocket broadcaster tested with multiple parallel clients. |
| **Dashboard** | Streamlit renders widgets and plots histories. | **PASS** | Correctly maps states to colors. |
| **Test Suite** | Unit test suite runs successfully. | **PASS** | 156/156 tests passing. |
| **Metric Lineage** | Conflicting metrics audited and locked. | **PASS** | Verified metrics locked in `final_verified_metrics.json`. |
| **Scientific Claims** | Exploratory and invalidated states documented. | **PASS** | Validated OOD limits and 0% HABSOS recall preserved. |
| **Documentation** | Reports and viva prep files generated. | **PASS** | 75 viva QA, demo script, and system diagrams compiled. |
| **Demo Setup** | Demo launcher verified. | **PASS** | `run_demo.py` spins up all modules in parallel. |
| **Limitations** | Manifest lists all active constraints. | **PASS** | Verified in `release_manifest.json`. |
| **Release Manifest** | Configuration freeze manifest generated. | **PASS** | Version frozen at `1.0.0`. |
