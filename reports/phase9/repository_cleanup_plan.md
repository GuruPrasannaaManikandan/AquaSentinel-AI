# Repository Cleanup Plan

This document details the cleanup classification applied to the Capstone repository before release freeze.

## 1. File Classifications

We catalog project files into four categories:
1.  **KEEP:** Critical source, configuration, database, test, and documentation modules.
2.  **ARCHIVE:** Historical forensic evidence (Phase 4 invalid pipelines, Phase 4.5 audit reports).
3.  **DELETE_SAFE:** Temporary cache files and local test-generated databases.
4.  **MANUAL_REVIEW:** Stale files requiring user checking.

---

## 2. Inventory Classification Listing

### 2.1 KEEP (Preserved for release)
*   All modules under `src/`.
*   All dashboards under `dashboard/`.
*   Deployment models: `models/deployment/caml_champion.joblib`, `models/deployment/habsos_champion.joblib`.
*   AIS models: `models/ais/caml_nsa.joblib`, `models/ais/habsos_nsa.joblib`.
*   Gateway DB: `models/fusion/aquatic_events.db`.
*   Release configs: `config/device_registry.json`, `config/sensor_feature_mapping.json`, `config/fusion_policy.json`.

### 2.2 ARCHIVE (Preserved forensic evidence)
*   Invalid models: `models/archive/phase4_invalid/`.
*   Audit reports: `reports/phase45/model_recovery_report.md`.

### 2.3 DELETE_SAFE (Cleaned during Phase 9 step)
*   Temporary databases: `models/fusion/test_events.db`, `models/fusion/test_phase8_events.db` (automatically deleted after test suites tear down).
*   Temporary scratch files: `scratch/check_distances.py`, `scratch/analyze_confidence.py` (archived to `scratch/archive/`).

---

## 3. Safe Cleanup Actions
*   Verified that all temporary SQLite `.db` test logs have been deleted.
*   Archived scratch scripts to prevent directory clutter.
