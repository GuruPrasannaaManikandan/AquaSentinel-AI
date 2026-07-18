# Report 11: Final Dataset Verdict

This report classifies the suitability of the AE2426 dataset for various applications within the Capstone project.

## Classification Table

| Domain / Task | Verdict | Evidence / Justification |
|---|---|---|
| **Existing CAML Retraining** | **INVALID** | CAML is a freshwater ML model. AE2426 is a marine dataset. The optical, biological, and chemical regimes are completely incompatible. |
| **Existing HABSOS Retraining** | **NOT RECOMMENDED** | HABSOS is trained on GoM HAB indicators. AE2426 is from the North East Shelf and lacks bloom/species classification labels. |
| **Direct Model Merging** | **INVALID** | Merging this data violates the active release freeze. The schemas, feature lists, and targets are entirely different. |
| **Supervised ML (Regression)** | **NOT RECOMMENDED** | The matched sample size ($N=11$) is far too small to train generalizeable supervised models. Any model will overfit. |
| **Unsupervised ML (PCA/Clustering)** | **USEFUL** | PCA and clustering can successfully reduce the 551 wavelengths to 2-3 components, capturing cross-shelf optical transitions. |
| **AIS (OOD Detection)** | **USEFUL** | The Negative Selection Algorithm (NSA) can use CDOM spectra to train self-detectors and flag optical anomalies in real-time. |
| **Spectral Analysis (Optical Indices)** | **EXCELLENT** | The 1 nm resolution from 300 to 850 nm is ideal for calculating spectral slopes ($S_{275-295}$, $S_{350-400}$) and Slope Ratios ($S_R$). |
| **IoT Simulation** | **USEFUL** | The 12 spectral samples provide excellent telemetry templates for simulating a virtual multispectral spectrophotometer sensor. |
| **Future Hardware Design** | **USEFUL** | The dataset can guide the selection of discrete band filters for designing a low-cost multispectral sensor (e.g., AS7341). |
| **Dashboard Visualization** | **USEFUL** | Displays of spectral decay curves and PCA projections add significant educational and visual value to the UI. |
| **Research-Paper Value** | **USEFUL** | Serves as a strong exploratory case study for expanding IoT aquatic nodes to include optical/spectral evidence. |
| **Capstone Future-Work Value** | **EXCELLENT** | Provides the precise scientific foundation needed to develop an "Optical Sensing Branch" in the next phase of the project. |

---

## Actionable Recommendations
1. **Maintain Release Freeze**: Do not retrain or alter any active code or database.
2. **Develop Anomaly Detectors**: Use the CDOM wide-format dataset to train an offline One-Class classifier (such as an Isolation Forest or a Negative Selection detector) to detect the Station 20 coastal anomaly.
3. **Simulate virtual sensors**: Add an ESP32 simulator branch that reads `cdom_wide.csv` and publishes multispectral band subsets (412nm, 443nm, 480nm, 555nm, 670nm) via MQTT.
4. **Use as Future Work Foundation**: Include these findings in the capstone's final presentation as the core proposal for Phase 10 (multimodal optical expansion).
