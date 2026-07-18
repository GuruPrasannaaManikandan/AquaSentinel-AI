# Report 09: Existing Capstone Compatibility Audit

This report evaluates how the AE2426 dataset relates to the existing Capstone system and outlines a future integration architecture.

## Capstone Compatibility Answers

### 1. Can AE2426 improve CAML?
**No.** The CAML model is a supervised ML model trained on freshwater lakes/reservoirs data (for cyanobacteria abundance). AE2426 is an offshore marine dataset (North East Shelf). These ecosystems have completely different optical signatures, salinity profiles, and phytoplankton community structures.

### 2. Can AE2426 improve HABSOS?
**No.** HABSOS is a marine ML model, but it is trained on Gulf of Mexico HAB events with specific binary labels. AE2426 does not contain HAB bloom labels or the same features, so it cannot be used to train or improve HABSOS directly.

### 3. Can AE2426 be merged directly?
**No.** The existing project is release-frozen. Merging this dataset directly into the active databases or model registries would violate the release freeze and corrupt the validated pipelines.

### 4. Can it support an independent optical analysis module?
**Yes.** In a future version, the system can support a parallel, independent "Optical Sensing Module" that processes spectral datasets without affecting the existing CAML/HABSOS branches.

### 5. Can it support AIS anomaly detection?
**Yes.** The Negative Selection Algorithm (NSA) in the current Artificial Immune System (AIS) can be extended to accept normalized CDOM absorption values (or PCA coordinates) to detect OOD (Out-of-Distribution) optical anomalies.

### 6. Can it support a virtual optical sensor?
**Yes.** We can update the ESP32 finite-state-machine and MQTT simulation to include a virtual "Spectrophotometer Sensor". It would publish spectral bands (e.g. at 412, 443, 490, 555, 670 nm) via MQTT to the gateway, simulating real-time optical data transmission.

### 7. What real hardware would be required?
To collect CDOM and absorbance data in the field, we would need:
- An in-situ spectrophotometer (e.g., Sea-Bird WET Labs AC-S or AC-9) that measures absorption and attenuation at multiple wavelengths.
- Alternatively, a field-deployable fluorometer (e.g., Turner Designs Cyclops-7F) tuned specifically to CDOM/FDOM (fluorescent dissolved organic matter).

### 8. Could lower-cost optical sensors approximate any measurements?
**Yes.** Instead of a full 551-wavelength spectrophotometer, a low-cost multispectral sensor chip like the **AS7341** (11 channels) or **AS7262** (6 channels) could be integrated with the ESP32. By measuring light absorption at key bands (415 nm, 445 nm, 480 nm, 515 nm, 555 nm, 680 nm), it can approximate the CDOM exponential decay curve.

### 9. Which features could theoretically map to IoT sensors?
- Absorption coefficients at specific wavelengths ($a_g(412)$, $a_g(443)$) measured in-situ by optical sensors.
- Derived FDOM fluorescence values.
- Standard environmental metadata (temperature, salinity, depth).

### 10. Which features require laboratory instrumentation?
All HPLC pigment concentrations (e.g., `Tot_Chl_a`, `Fuco`, `Zea`, `Lut`, `Neo`) require laboratory instrumentation.

### 11. Is HPLC deployable as an IoT sensor? Explain why or why not.
**No, HPLC is NOT deployable as an IoT sensor.** 
- *Explanation*: High-Performance Liquid Chromatography (HPLC) is a destructive, high-precision laboratory analytical technique. It requires collecting water samples, filtering them onto glass fiber filters, freezing them in liquid nitrogen, extracting the pigments using organic solvents (like acetone or methanol), and injecting the extract into a high-pressure chromatography column under controlled temperature and chemical gradients. This requires heavy lab equipment, toxic reagents, high power, and skilled technicians, making it impossible to deploy as an autonomous, low-power in-situ IoT sensor.

### 12. How could the dashboard display spectral information?
The Streamlit dashboard could include:
- A spectral line chart displaying the $a_g(\lambda)$ vs wavelength curve for the active sample.
- A 2D PCA scatter plot showing where the active sample lies relative to the historical baseline cluster, highlighting OOD anomalies.
- A bar chart of major pigment groups estimated from the optical proxy.

### 13. How could the fusion engine incorporate optical evidence in a future version?
The Dempster-Shafer Evidence Fusion Engine can be updated to include a new focal element: **Optical Anomaly Probability** (derived from the spectral AIS detector). This would fuse with physical evidence (CAML, HABSOS, temperature, dissolved oxygen) to compute a more comprehensive "Ecosystem Distress Index".

---

## Future Multi-Branch Architecture

```mermaid
graph TD
    subgraph IoT Edge (ESP32 Simulation)
        Sensors["Physical Sensors (Temp, DO, pH)"]
        OptSensor["Virtual Spectrophotometer (AS7341)"]
    end
    
    Gateway["IoT Gateway (MQTT Broker)"]
    Sensors -->|MQTT| Gateway
    OptSensor -->|MQTT| Gateway
    
    subgraph FastAPI Backend
        Fusion["Evidence Fusion Engine (Dempster-Shafer)"]
        
        subgraph Physical ML
            CAML["CAML (Freshwater ML)"]
            HABSOS["HABSOS (Marine ML)"]
        end
        
        subgraph Optical ML (Future)
            OptAIS["Spectral AIS (Negative Selection)"]
            OptProxy["Optical Proxy (PLS Regression)"]
        end
    end
    
    Gateway --> CAML
    Gateway --> HABSOS
    Gateway --> OptAIS
    Gateway --> OptProxy
    
    CAML -->|Belief Mass| Fusion
    HABSOS -->|Belief Mass| Fusion
    OptAIS -->|Optical Anomaly Mass| Fusion
    
    subgraph Client Application
        Dashboard["Streamlit Dashboard"]
    end
    
    Fusion -->|Ecosystem Status| Dashboard
    OptProxy -->|Pigment Profiles| Dashboard
    OptAIS -->|Spectral Outliers| Dashboard
```
