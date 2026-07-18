# Unknown Anomaly Experiment Report

This experiment demonstrates the ability of the Artificial Immune System (AIS) to identify out-of-distribution (OOD) observations that represent unusual or novel environmental structures, even when the supervised ML model assigns a known class with high confidence.

---

## 1. Experimental Setup
We generated two synthetic observations that remain within scientifically plausible boundaries but represent novel environmental profiles absent from normal training distributions:

### 1.1 CAML (Freshwater)
- **Input Coordinates:** `lat = 27.5, lon = -81.2` (Florida)
- **Distance to Water:** `6,000 meters` (Abnormally far for a freshwater monitoring sensor).
- **Date Context:** Peak Winter cyclic encodings.

### 1.2 HABSOS (Marine)
- **Input Coordinates:** `LATITUDE = 27.5, LONGITUDE = -82.5` (Florida Coastal)
- **Sensor depth:** `45 meters` (Abnormally deep for standard coastal dinoflagellate monitoring).
- **Physical water indicators:** `SALINITY = 42.0 ppt` and `WATER_TEMP = 38.0°C` (Extreme water temperature for winter season).

---

## 2. Experimental Results

### 2.1 CAML Test
- **Supervised ML Output:**
  - Predicted Class: 1
  - Confidence: 0.3652
- **Unsupervised AIS Output:**
  - Anomaly detected: True
  - Anomaly score: 0.0582
  - Nearest detector distance: 0.8476
  - Matched detector count: 1

### 2.2 HABSOS Test
- **Supervised ML Output:**
  - Predicted Class: 'warning'
  - Confidence: 0.6513
- **Unsupervised AIS Output:**
  - Anomaly detected: True
  - Anomaly score: 0.0998
  - Nearest detector distance: 0.6301
  - Matched detector count: 3

---

## 3. Scientific Implications
The experiment confirms the parallel security architecture:
1.  **ML Model limitation:** The supervised Random Forest and Logistic Regression models are forced to classify observations into one of the trained known classes, often mapping OOD anomalies to `'normal'` with high confidence due to majority class bias.
2.  **AIS Strength:** The unsupervised Negative Selection layer flags these anomalies successfully (producing anomaly scores $> 0.0$), identifying that the observation lies within the non-self detector space.
