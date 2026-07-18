# Feature Eligibility & Data Leakage Audit Report

This report audits every column in both datasets to identify target leakage hazards, administrative metadata, and availability during real-time IoT inference.

---

## 1. CAML Feature Eligibility Table

| Column Name | Data Type | Classification | Real-Time IoT Availability | Recommendation | Reason / Justification |
| --- | --- | --- | --- | --- | --- |
| `uid` | object | Identifier | No | **DROP** | Unique record ID. Carrying no predictive information, it leads to index memorization. |
| `data_provider` | object | Metadata | No | **DROP** | High-cardinality label of reporting agency. Keeping it causes spatial-agency leakage. |
| `region` | object | Metadata | Yes | **RETAIN** | Coarse geographical region (e.g. northeast, midwest, west). Useful broad spatial category. |
| `lat` | float64 | Valid Predictor | Yes (GPS) | **RETAIN** | Geographic latitude. Critical for identifying localized historical risk pools. |
| `lon` | float64 | Valid Predictor | Yes (GPS) | **RETAIN** | Geographic longitude. Critical for identifying localized historical risk pools. |
| `date` | int64 | Metadata | Yes (System Clock) | **DROP / EXTRACT**| Raw `yyyymmdd` integer. Feeding directly causes overfitting to temporal progressions. Extract Month and Season instead. |
| `time` | object | Metadata | Yes (System Clock) | **DROP** | Raw timestamp. Highly incomplete, does not carry seasonal significance. |
| `abun` | float64 | Target Leakage | No | **DROP (Feature)** | Continuous abundance count in cells/L. Deterministically defines the target `severity`. Including it causes trivial target leakage. |
| `severity` | int64 | Target | No | **RETAIN (Target)** | Classification target variable representing bloom hazard (levels 1-5). |
| `distance_to_water_m` | float64 | Valid Predictor | Yes (GIS / Lookup) | **RETAIN** | Continuous distance to shoreline in meters. Critical for predicting cyanobacteria pooling. |

---

## 2. HABSOS Feature Eligibility Table

| Column Name | Classification | Real-Time IoT Availability | Recommendation | Reason / Justification |
| --- | --- | --- | --- | --- | --- |
| `STATE_ID` | Metadata | Yes (GIS / Config) | **RETAIN** | State code (FL, TX, AL, MS). Helps model geographic/administrative partitions. |
| `DESCRIPTION` | Metadata | No | **DROP** | Textual location descriptions (e.g. "Copano Bay 2"). High cardinality, non-numeric. |
| `LATITUDE` | Valid Predictor | Yes (GPS) | **RETAIN** | Latitude coordinates. Crucial for spatial routing. |
| `LONGITUDE` | Valid Predictor | Yes (GPS) | **RETAIN** | Longitude coordinates. Crucial for spatial routing. |
| `SAMPLE_DATE` | Metadata | Yes (System Clock) | **DROP / EXTRACT**| Raw date string. Drop after extracting `Month` and `Season`. |
| `SAMPLE_TIME` | Metadata | Yes (System Clock) | **DROP** | Raw time. Missing in 23% of rows, redundant with date features. |
| `SAMPLE_DEPTH` | Valid Predictor | Yes (Sensor) | **RETAIN** | Depth of water sample. Crucial physical factor; default to 0 (surface) if null. |
| `GENUS` | Constant | No | **DROP** | 100% constant value (`Karenia`). |
| `SPECIES` | Constant | No | **DROP** | 100% constant value (`brevis`). |
| `CATEGORY` | Target | No | **RETAIN (Target)** | Classification target representing bloom category. |
| `CELLCOUNT` | Target Leakage | No | **DROP (Feature)** | Continuous cell count. Deterministically defines `CATEGORY`, causing target leakage. |
| `CELLCOUNT_UNIT`| Constant | No | **DROP** | 100% constant value (`cells/L`). |
| `CELLCOUNT_QA` | Post-Outcome | No | **DROP** | Post-collection data quality flag. |
| `SALINITY` | Valid Predictor | Yes (Sensor) | **RETAIN** | Water salinity in PPT. Vital environmental predictor. |
| `SALINITY_UNIT` | Constant | No | **DROP** | 100% constant (`Parts Per Thousand`). |
| `SALINITY_QA` | Post-Outcome | No | **DROP** | Post-collection quality flag. |
| `WATER_TEMP` | Valid Predictor | Yes (Sensor) | **RETAIN** | Water temperature in Celsius. Vital environmental predictor. |
| `WATER_TEMP_UNIT`| Constant | No | **DROP** | 100% constant (`Celsius`). |
| `WATER_TEMP_QA` | Post-Outcome | No | **DROP** | Post-collection quality flag. |
| `WIND_DIR` | Valid Predictor | Yes (Sensor) | **DROP** | Wind direction. Dropped due to >99.5% missingness. |
| `WIND_DIR_QA` | Post-Outcome | No | **DROP** | Quality flag. |
| `WIND_SPEED` | Valid Predictor | Yes (Sensor) | **DROP** | Wind speed. Dropped due to >99.0% missingness. |
| `WIND_SPEED_QA` | Post-Outcome | No | **DROP** | Quality flag. |
| `OBJECTID` | Identifier | No | **DROP** | Database index identifier. |
| `Unnamed: 2` / `27`| Empty | No | **DROP** | 100% null columns. |

---

## 3. Real-Time IoT Inference Alignment

At inference time, the virtual IoT gateway will feed simulated sensor streams. Here is how they map to our model features:

*   **Virtual IoT Temp Sensor** $\rightarrow$ maps to **`WATER_TEMP`** in HABSOS model.
*   **Virtual IoT Salinity Sensor** $\rightarrow$ maps to **`SALINITY`** in HABSOS model.
*   **Virtual IoT Depth Sensor** $\rightarrow$ maps to **`SAMPLE_DEPTH`** in HABSOS model.
*   **Virtual IoT GPS Module** $\rightarrow$ maps to **`lat`/`lon`** (CAML) and **`LATITUDE`/`LONGITUDE`** (HABSOS).
*   **Virtual IoT RTC (Real Time Clock)** $\rightarrow$ maps to **`Month`** and **`Season`** cyclic features.

> [!NOTE]
> *pH, Turbidity, and Dissolved Oxygen* are highly relevant sensors for water quality. However, they are absent from the historical datasets. We will design the backend and simulator interfaces to allow future incorporation of these variables, but the current ML models will not consume them to prevent structural model errors.
