# AIS Feasibility Analysis Report

This report evaluates the feasibility of applying the Negative Selection Algorithm (NSA) to the freshwater (CAML) and marine (HABSOS) datasets, detailing the selection of distance spaces, features, coordinates, and architectures.

---

## 1. Architectural Independence: Separate AIS Models
The environmental profiles of freshwater lakes (CAML) and marine coastlines (HABSOS) are fundamentally distinct. Marine systems require physical parameters like salinity and water depth, which are absent in CAML. Therefore, **separate, independent AIS models are required** for CAML and HABSOS. They will have different feature schemas, target bounds, and hyperparameters.

---

## 2. CAML Feasibility Assessment (Freshwater Cyanobacteria)

### 2.1 SELF and NON-SELF Definition
*   **Target Column:** `severity` (discrete levels 1 to 5, mapping to cyanobacteria cell count abundance).
*   **Scientific SELF:** Severity Class `1` (abundance $< 20$ cells/L). This represents background, non-bloom, healthy aquatic conditions.
*   **Scientific NON-SELF:** Severity Classes `4` and `5` (abundance $\ge 1,000$ cells/L), representing high and extreme bloom threats.
*   *Note on Classes 2 & 3:* These classes represent intermediate levels (mild/medium blooms). To ensure a clean and unpolluted training representation of SELF, they are **excluded** from the training SELF set.

### 2.2 Feature Assessment
*   **Distance Calculation Suitability:** Geographic and temporal cyclic numerical features are suitable.
*   **Features Selected:** `['lat', 'lon', 'distance_to_water_m', 'Month_sin', 'Month_cos', 'DayOfYear_sin', 'DayOfYear_cos']`.
*   **Categorical Features Excluded:** `region` and `Season` are excluded. One-hot encoding them creates sparse, binary dimensions that distort continuous Euclidean and Manhattan distance metrics.
*   **Geographic Coordinates:** `lat` and `lon` are included. Cyanobacteria blooms are highly localized geographically; geographic bounds are essential to capture spatial normal SELF conditions.
*   **Temporal Cyclic Features:** `Month_sin`, `Month_cos`, `DayOfYear_sin`, and `DayOfYear_cos` are included. Blooms are highly seasonal. Normal conditions in Winter differ from Summer, making seasonal cyclic coordinates necessary.
*   **Missing-Value Indicators:** CAML has virtually no missing values in these fields, so missing-value indicators are excluded.
*   **Feature Scaling:** Required. `distance_to_water_m` ranges up to thousands of meters, which would dominate the distance space. A fitted `MinMaxScaler` maps all inputs to $[0, 1]$, making the distance metrics uniform.

---

## 3. HABSOS Feasibility Assessment (Marine HABs)

### 3.1 SELF and NON-SELF Definition
*   **Target Column:** `CATEGORY` (discrete labels `'normal'`, `'warning'`, `'critical'`).
*   **Scientific SELF:** `'normal'` category (combining raw categories `'not observed'` and `'very low'`). This represents baseline, safe marine conditions.
*   **Scientific NON-SELF:** `'warning'` and `'critical'` categories (combining raw categories `'low'`, `'medium'`, and `'high'`). These denote harmful levels of algal concentration.

### 3.2 Feature Assessment
*   **Distance Calculation Suitability:** Chemical-physical water measurements are highly suitable.
*   **Features Selected:** `['LATITUDE', 'LONGITUDE', 'SAMPLE_DEPTH', 'SALINITY', 'WATER_TEMP', 'Month_sin', 'Month_cos', 'DayOfYear_sin', 'DayOfYear_cos']`.
*   **Categorical Features Excluded:** `STATE_ID` and `Season` are excluded to avoid distance space distortion.
*   **Geographic Coordinates:** `LATITUDE` and `LONGITUDE` are included. Marine blooms are highly sensitive to spatial characteristics (e.g., wind-driven bays vs. open sea).
*   **Temporal Cyclic Features:** Included. Water temperature and nutrient cycles fluctuate seasonally, making temporal cyclic features crucial.
*   **Missing-Value Indicators:** `SALINITY_is_missing` and `WATER_TEMP_is_missing` are **excluded** from the distance space. Standard-scaling or scaling binary indicators introduces artificial offsets in distance metrics. Missing temperature/salinity values will be imputed, and distance will be calculated purely on the imputed physical values.
*   **Feature Scaling:** Required. Salinity ranges from 0 to 40+ ppt, while depth is in meters. Mapping all features to $[0, 1]$ via `MinMaxScaler` ensures distance threshold consistency.
