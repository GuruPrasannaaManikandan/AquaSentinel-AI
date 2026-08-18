# Version 4.3 — Computer Vision Dataset Audit & Model Training Plan

**Date**: 2026-08-17  
**Status**: **CASE B — NO TRAINED CV MODEL OR IMAGE DATASET FOUND IN REPOSITORY**

---

## 1. Repository Model & Dataset Audit Results

A recursive search across all directories in the project workspace (`models/`, `data/`, `src/`, `config/`, `reports/`) yielded the following empirical findings:

### A. Model Files Audit (`.pt`, `.pth`, `.onnx`, `.tflite`, `.keras`, `.h5`, `.weights`)
- **Found**: **0 Binary CV Weight Files**.
- **Existing Models**: All serialized `.joblib` files in `models/deployment/` (`caml_champion.joblib`, `habsos_champion.joblib`) and `models/ais/` (`caml_nsa.joblib`, `habsos_nsa.joblib`) are tabular ML classifiers (XGBoost/RandomForest) and unsupervised AIS anomaly detectors trained exclusively on numerical sensor parameters (pH, temperature, dissolved oxygen, chlorophyll-a, turbidity).

### B. Image Dataset Audit (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.xml`, `.txt`, `.json`)
- **Found**: **0 Aquatic Image Datasets**.
- **Existing Datasets**: All datasets in `data/raw/` and `data/processed/` (`caml_train.csv`, `habsos_train.csv`, etc.) are tabular numerical sensor CSV files.

---

## 2. Applicable Case: CASE B (No Genuine Model or Image Dataset Found)

Per project directives for CASE B:
- **No Model Fabrication**: No synthetic weights, fabricated metrics, or unrelated generic models (e.g. COCO object detectors) are declared as the project's trained aquatic bloom model.
- **Current State**: The V4 pipeline architecture (`CameraFrame` → `ImagePreprocessor` → `BaseCVModel` interface → `CVPrediction` → `VisualDetector` → `VisualEvidence`) is fully implemented, hardware-ready, and functionally verified with 212/212 passing regression tests. However, the model engine in `src/cv/cv_model.py` requires real binary model weights.

---

## 3. Recommended Computer Vision Training Pipeline Plan

To train a genuine visual aquatic bloom model, the following training pipeline is specified:

### A. Dataset Acquisition Requirements
- **Target Classes**:
  1. `NO_BLOOM`: Normal clear aquatic water images.
  2. `ALGAL_BLOOM_RISK`: Microalgae/cyanobacteria surface accumulation (green/cyan scum).
  3. `TURBID_DISCOLORATION`: High suspended sediment / discolored water.
- **Recommended Data Sources**:
  - Roboflow Aquatic Algae / Water Quality Vision Datasets (e.g., Algae Bloom Detection Dataset).
  - EPA / NOAA Water Surface Microscopic & Field Imagery.

### B. Target Model Architecture
- **Model Framework**: Ultralytics YOLOv8 / YOLOv11 Lightweight Object Detector (`yolov8n.pt` / `yolov8s.pt` nano/small backbone) or MobileNetV3 Classifier.
- **Export Format**: ONNX (`.onnx`) or PyTorch (`.pt`) for host/gateway edge inference.
- **Input Contract**: `224x224x3` (or `640x640x3`), `RGB`, `float32`, `RESCALE [0.0, 1.0]`.

### C. Training & Export Steps (To be executed when image dataset is supplied)
1. Organize images into `data/cv_raw/train`, `data/cv_raw/val`, `data/cv_raw/test` with standard YOLO `.txt` bounding box annotations or class directories.
2. Train model via Ultralytics API:
   ```python
   from ultralytics import YOLO
   model = YOLO('yolov8n.pt')
   model.train(data='data/cv_raw/data.yaml', epochs=50, imgsz=224)
   model.export(format='onnx', dynamic=True)
   ```
3. Save trained weights file to `models/cv/aquatic_bloom_yolov8n.onnx`.
4. Update `AquaticBloomCVModel` in `src/cv/cv_model.py` to load `models/cv/aquatic_bloom_yolov8n.onnx` using `onnxruntime.InferenceSession`.
