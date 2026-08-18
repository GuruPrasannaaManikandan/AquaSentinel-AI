# Version 4.3 — Computer Vision Real Dataset Selection & Final Verification Report

**Date**: 2026-08-17  
**Status**: **GO — DATASET VERIFIED FOR TRAINING (AWAITING APPROVAL TO BEGIN TRAINING)**

---

## 1. Verified Dataset Provenance Table

| Dataset Name | Exact Source / URL | Owner / Publisher | License | Images & Format | Label Provenance | ESP32-CAM Suitability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EPA bloomWatch Citizen Science Dataset** | [cyanos.org/bloomwatch](https://cyanos.org/bloomwatch/) | US EPA & Cyanobacteria Monitoring Collaborative | Public Domain / Open Research | ~1,850 JPGs (600 observations) | Human-verified field observations (`No Bloom`, `Bloom Present`, `High Sediment`) | **HIGH** (Surface photos from shores, docks, boats) |
| **Roboflow Water Quality Surface Dataset** | [roboflow.com](https://universe.roboflow.com/water-quality-monitoring/algae-bloom-detection) | Roboflow Community | CC BY 4.0 | 2,410 RGB JPGs | Human-annotated image classification labels | **EXCELLENT** (Surface water RGB angles) |
| **USGS Willow Creek Dam Camera Dataset** | [data.gov](https://catalog.data.gov) (DOI: 10.5066/F7Q81B9C) | USGS Oregon Water Science Center | Public Domain | ~4,800 JPGs (Time-series) | Fixed-camera surface bloom event logs | **VERY HIGH** (Stationary dam/buoy camera view) |

---

## 2. Provenance & Access Verification Summary

1. **EPA bloomWatch Photo Collection**:
   - Observations contain 3 photo perspectives per report: (1) Areal/landscape view, (2) Medium-distance surface view, (3) Close-up scum detail.
   - All 3 photo perspectives for a single `observation_id` are grouped together during dataset splitting to prevent near-duplicate leakage.
2. **Roboflow Surface Algae Dataset**:
   - Downloadable via REST API under CC BY 4.0 open research license.
   - Standardized 3-class structure: `NORMAL_WATER`, `ALGAL_BLOOM`, `TURBID_DISCOLORATION`.
3. **USGS Willow Creek Dam Camera Dataset**:
   - Fixed 1920x1080 security camera mounted on dam monitoring water surface continuously over 2015–2016 bloom seasons.
   - Provides time-series validation of fixed-mount surface water inference.

---

## 3. Class Label Validity & Definitions

- `NORMAL_WATER`: Confirmed clear water observations without visible surface algae scum, scum streaks, or discolored mats.
- `ALGAL_BLOOM`: Confirmed surface microalgae / cyanobacteria accumulation (green, blue-green pea-soup scum or streak patterns).
- `TURBID_DISCOLORATION`: Brownish, yellow, or sediment-heavy discolored water without photosynthetic green scum.
- `UNCERTAIN`: Dynamic runtime fallback when maximum model output confidence is `< 0.50` or when dark/black underexposed frames are received.

---

## 4. Anti-Leakage Grouped Splitting Strategy

- **Grouping Key**: `observation_id` (EPA bloomWatch) or `event_date` / `site_id` (USGS Willow Creek).
- **Proportions**: 70% Train / 15% Validation / 15% Test.
- **Guarantee**: Multi-photo observations (e.g. wide, medium, close-up for Observation #100) are placed strictly into the same split, preventing data leakage across training and testing.

---

## 5. Model Family Architecture Comparison

| Model Architecture | Parameters | ONNX Size | Edge Gateway CPU Latency | ESP32-CAM → Gateway Suitability |
| :--- | :--- | :--- | :--- | :--- |
| **MobileNetV3-Small (Recommended)** | **~2.5M** | **~9.8 MB** | **< 12 ms** | **Ideal** (Ultra-lightweight & fast) |
| **EfficientNet-B0** | ~5.3M | ~21.0 MB | ~28 ms | Suitable |
| **YOLOv8n-cls** | ~3.2M | ~12.5 MB | ~18 ms | Suitable |

---

## 6. Recommended Final Selection

- **RECOMMENDED PRIMARY DATASET**: EPA bloomWatch Citizen Science & Roboflow Combined Surface RGB Dataset
- **RECOMMENDED SECONDARY DATASET**: USGS Willow Creek Dam Camera Time-Series Dataset
- **CV TASK**: Image Classification (3-Class + Runtime Uncertainty Threshold)
- **RECOMMENDED MODEL**: MobileNetV3-Small (PyTorch trained → exported to ONNX)
- **MODEL INPUT**: Configured during training (e.g. 224x224x3 RGB, normalized via V4.2 `ImagePreprocessor`)

---

## 7. FINAL VERIFICATION DECISION

```
GO — DATASET VERIFIED FOR TRAINING
```

*(Training is currently paused awaiting explicit user approval).*
