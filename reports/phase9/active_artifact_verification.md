# Active Artifact Verification Report

This report confirms that all deployed artifacts exist, load successfully, maintain schema alignment, and do not reference invalidated files.

## 1. Verified Artifact Registry

| Component | Location | Validation Method | Version Check | Schema Matches |
|:---|:---|:---|:---|:---|
| **CAML ML Model** | `models/deployment/caml_champion.joblib` | Joblib load check. | `3.0.0` (Verified) | Yes |
| **HABSOS ML Model** | `models/deployment/habsos_champion.joblib` | Joblib load check. | `3.0.0` (Verified) | Yes |
| **CAML AIS Model** | `models/ais/caml_nsa.joblib` | Joblib load check. | `NSA-CAML-v1` (Verified) | Yes |
| **HABSOS AIS Model** | `models/ais/habsos_nsa.joblib` | Joblib load check. | `NSA-HABSOS-v1` (Verified) | Yes |
| **Fusion Policy** | `config/fusion_policy.json` | JSON schema parse check. | `1.0.0` (Verified) | Yes |
| **Device Registry** | `config/device_registry.json` | JSON schema parse check. | `1.0.0` (Verified) | Yes |
| **SQLite database** | `models/fusion/aquatic_events.db` | Schema exists check. | `v1` (Verified) | Yes |

---

## 2. Invalidation & Security Checks

*   **Invalidated Models Check:** Confirmed that the gateway loader and `DecisionPipeline` never load artifacts from `models/archive/phase4_invalid/`. Attempts to load models with status `INVALIDATED` or `FAILED_PHASE45_INTEGRITY_AUDIT` raise a `PermissionError`.
*   **Version Matches:** Registry records match manifest parameters.
*   **Dependency Tree Resolves:** Core packages (`pandas`, `numpy`, `scikit-learn`, `fastapi`, `streamlit`) resolve correctly.
