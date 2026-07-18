# Model Card: CAML Aquatic Warning Model

## 1. Intended Use
- **Primary Use Case:** Real-time prediction and categorization of toxic algae blooms for environmental monitoring gates.
- **Inappropriate Uses:** Predict human toxicity levels directly. Do not deploy in marine ecosystems if trained on CAML, and vice versa.

## 2. Training Dataset
- Dataset Source: CAML processed historical data.
- Input Features: ['lat', 'lon', 'distance_to_water_m', 'region', 'Season', 'Year', 'Month_sin', 'Month_cos', 'DayOfYear_sin', 'DayOfYear_cos']
- Preprocessing: Robust scaling, Group-based spatial-temporal median imputation, sin/cos month extraction.

## 3. Selected Model Architecture
- **Algorithm:** ThresholdShiftClassifier (Calibrated)
- **Locked Hyperparameters:** {'n_estimators': 50, 'min_samples_split': 5, 'max_depth': 14, 'class_weight': 'balanced'}

## 4. Performance Metrics
- **Validation Macro F1:** 0.5060
- **Validation Dangerous Recall:** 0.9359
- **Final Test Macro F1:** 0.4837
- **Final Test Dangerous Recall:** 0.9097

## 5. Limitations & Failure Modes
- Underperforms during sudden, unseasonable climate changes (e.g. unseasonably cold summers).
- Relies on spatial coordinates; predictions may drift if deployed in geographic coordinates outside the training boundaries.
