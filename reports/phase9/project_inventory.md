# Project Inventory Report

This report catalogs all source code, datasets, registry metadata, database tables, and reports within the Capstone project.

## 1. Project Directory Structure

```text
├── config/
│   ├── sensor_feature_mapping.json
│   └── device_registry.json
├── dashboard/
│   └── app.py
├── docs/
├── models/
│   ├── deployment/
│   │   ├── model_manifest.json
│   │   ├── caml_champion.joblib
│   │   └── habsos_champion.joblib
│   ├── ais/
│   │   ├── ais_registry.json
│   │   ├── caml_nsa.joblib
│   │   └── habsos_nsa.joblib
│   ├── fusion/
│   │   ├── fusion_registry.json
│   │   └── aquatic_events.db
│   └── archive/
│       └── phase4_invalid/
├── reports/
├── src/
│   ├── models/
│   │   └── deployment_loader.py
│   ├── ais/
│   │   ├── preprocessing.py
│   │   ├── affinity.py
│   │   ├── negative_selection.py
│   │   ├── ais_loader.py
│   │   └── parallel_inference.py
│   ├── fusion/
│   │   ├── fusion_engine.py
│   │   └── decision_pipeline.py
│   ├── iot/
│   │   ├── sensor_simulator.py
│   │   ├── edge_validation.py
│   │   ├── mqtt_client.py
│   │   ├── actuators.py
│   │   ├── esp32_device.py
│   │   └── event_store.py
│   └── backend/
│       ├── schemas.py
│       ├── alerts.py
│       ├── services.py
│       └── app.py
├── tests/
├── README.md
├── requirements.txt
├── run_demo.py
├── run_phase5.py
├── run_phase6.py
├── run_phase7.py
├── run_phase8.py
└── run_phase9.py
```

---

## 2. Key Artifact Details

| Artifact Name | Location | Purpose | Status | Dependencies |
|:---|:---|:---|:---|:---|
| **CAML ML Model** | `models/deployment/caml_champion.joblib` | Weighted RF classification. | ACTIVE | `deployment_loader.py` |
| **HABSOS ML Model** | `models/deployment/habsos_champion.joblib` | Weighted LR classification. | ACTIVE | `deployment_loader.py` |
| **CAML AIS Model** | `models/ais/caml_nsa.joblib` | Freshwater NSA anomaly novelty filter. | ACTIVE | `ais_loader.py` |
| **HABSOS AIS Model** | `models/ais/habsos_nsa.joblib` | Marine NSA anomaly novelty filter. | ACTIVE | `ais_loader.py` |
| **Events Database** | `models/fusion/aquatic_events.db` | Logs telemetry, validation, decisions. | ACTIVE | `event_store.py` |
| **FastAPI Backend** | `src/backend/app.py` | REST endpoints and WS connections. | ACTIVE | `services.py` |
| **Streamlit UI** | `dashboard/app.py` | System KPI gauges and trends interface. | ACTIVE | FastAPI Endpoints |
| **Archived Models** | `models/archive/phase4_invalid/` | Invalid Phase 4 optimization pipelines. | **INACTIVE** | None |

---

## 3. Clutter & Temporary Files
The cleanup audit identified the following stale items for archiving or deletion:
*   *Stale SQLite DB files:* `test_events.db`, `test_phase8_events.db` (safe to delete after test teardowns).
*   *Scratch Scripts:* `scratch/check_distances.py`, `scratch/analyze_confidence.py` (archived to `scratch/archive/`).
