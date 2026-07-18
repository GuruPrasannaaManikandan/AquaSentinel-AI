# AIS Interface Specification Document

This document defines the data schema exposed by the machine learning pipeline to feed the downstream Artificial Immune System (AIS) decision validation layer.

---

## 1. Gateway Processing Flow
```
ML Pipeline Inference
   ↓ (Calculates classification and probabilities)
JSON Inference Payload
   ↓ (Exposes inputs, predictions, and max probabilities)
AIS Gateway Validator
   ↓ (Runs negative-selection anomaly match against antigen profiles)
Final Validated Warning Output
```

## 2. JSON Payload Schema Spec
For every prediction run on the edge gateway, the ML model wraps the output into the following JSON schema:

```json
{
    "timestamp": "2026-07-08T00:00:00Z",
    "prediction": {
        "predicted_class": 4,
        "max_confidence": 0.765,
        "probabilities": {
            "1": 0.02,
            "2": 0.08,
            "3": 0.135,
            "4": 0.765,
            "5": 0.00
        }
    },
    "feature_vector": {
        "lat": 27.234,
        "lon": -81.456,
        "distance_to_water_m": 43.2,
        "region": "FL",
        "Season": "Summer",
        "Year": 2026,
        "Month_sin": 0.5,
        "Month_cos": -0.866,
        "DayOfYear_sin": 0.35,
        "DayOfYear_cos": -0.93
    },
    "imputation_indicators": {
        "SAMPLE_DEPTH_imputed": false,
        "SALINITY_imputed": false,
        "WATER_TEMP_imputed": false
    }
}
```

## 3. AIS Input Consumer
The downstream AIS layer consumes this payload. If the `max_confidence` is low (e.g., < 0.65) or the feature vector represents an anomalous state (antigen detection), the AIS layer flags the prediction as highly uncertain and raises an alert.
