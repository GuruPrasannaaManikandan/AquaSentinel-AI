# Sensor-to-Model Feature Contract Report

This report documents the exact mapping of simulated sensor values to inference features and edge-side safety rules.

## 1. Feature Mapping Table

| Sensor | Telemetry JSON Field | CAML (Freshwater) Route | HABSOS (Marine) Route | Edge Rules | Rationale |
|:---|:---|:---|:---|:---|:---|
| **GPS Lat** | `location.latitude` | `lat` (Used by ML/AIS) | `LATITUDE` (Used by ML/AIS) | No | Direct spatial coordinate. |
| **GPS Lon** | `location.longitude` | `lon` (Used by ML/AIS) | `LONGITUDE` (Used by ML/AIS) | No | Direct spatial coordinate. |
| **Temp** | `sensors.temperature_c` | **EXCLUDED** | `WATER_TEMP` (Used by ML/AIS) | Yes | Marine models use temp for bloom likelihood. Freshwater model has no temp feature. |
| **Salinity** | `sensors.salinity_ppt` | **EXCLUDED** | `SALINITY` (Used by ML/AIS) | Yes | Marine models use salinity for dinoflagellate growth likelihood. Excluded from Freshwater. |
| **pH** | `sensors.ph` | **EXCLUDED** | **EXCLUDED** | Yes | Not in model training space; used for edge-side acid/base alerts. |
| **Turbidity** | `sensors.turbidity_ntu` | **EXCLUDED** | **EXCLUDED** | Yes | Not in model training space; used for edge-side clarity alerts. |
| **DO** | `sensors.dissolved_oxygen_mg_l` | **EXCLUDED** | **EXCLUDED** | Yes | Not in model training space; used for edge-side respiration/anoxia alerts. |

---

## 2. Ingestion Constraints

1.  **Exclusion Policy:** Unsupported sensor fields (e.g. pH, turbidity) must **never** be injected into the feature arrays passed to the ML/AIS loader models. Ingesting extra or misaligned dimensions will break model matrix calculations or lead to silent feature misalignment.
2.  **Imputation at Gateway:** If optional telemetry coordinates are missing, the gateway will impute using the device registry values before running inference.
3.  **Cyclic Seasonal Conversions:** Timestamps are split on the gateway using RTC values to produce `Month_sin`, `Month_cos`, `DayOfYear_sin`, and `DayOfYear_cos`.
