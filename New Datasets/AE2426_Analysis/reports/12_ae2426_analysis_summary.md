# Report 12: AE2426 Dataset Analysis Summary

This report provides a comprehensive summary of the forensic, scientific, and statistical analysis performed on the AE2426 dataset.

## 1. What was Downloaded?
We audited and processed the following items from the AE2426 dataset root:
- **12 CDOM spectral files** (`.sb` format) under `archive/` containing absorption scans.
- **1 HPLC pigment file** (`NES-LTER_AE2426_HPLC_20241106_1628_R1.sb`) under `archive/` containing 32 pigment sample profiles.
- **1 Documentation Archive** (`documents.tgz`), which was decompressed into `data/interim/documents/` and audited. It contains instrument checklists (RTFs), maps, scientific protocols (PDFs), and a master laboratory report (XLSX).

## 2. Scientific Terms Explained
- **CDOM (Chromophoric Dissolved Organic Matter)**: The fraction of dissolved organic matter in water that absorbs light in the ultraviolet and visible ranges. CDOM is a major optical constituent affecting water color and light availability in aquatic systems.
- **HPLC (High-Performance Liquid Chromatography)**: A high-precision laboratory technique used to separate and quantify individual phytoplankton pigments (e.g., Chlorophylls, Carotenoids). These pigments serve as biomarkers for identifying phytoplankton abundance and community structure.

## 3. Dataset Characteristics
- **Independent Samples**: There are exactly **12 independent CDOM physical water samples** (each represented by one file) and **32 HPLC samples**.
- **Measurements per Sample**: Each CDOM sample contains **551 measurements** corresponding to a 1 nm wavelength grid from 300 nm to 850 nm.
- **Total Data Rows**:
  - CDOM: 6,612 rows in long format (551 rows × 12 files).
  - HPLC: 32 rows representing 32 physical samples.
- **Major Variables**:
  - CDOM: `wavelength` (nm), `ag` (absorption coefficient, 1/m), `abs_ag` (absorbance).
  - HPLC: `Tot_Chl_a` (Total Chlorophyll-a), `Fuco` (Fucoxanthin), `Zea` (Zeaxanthin), `lat`, `lon`, `depth`.

## 4. Key Findings

### Data Quality
- **Negative Values**: CDOM spectra show negative values at longer wavelengths (>650 nm), representing spectrophotometer baseline noise.
- **Outliers**: Sample `NES-LTER_AE2426_ag_202411110643_003m_R1.sb` (Station 20, 3.3m) is an outlier, exhibiting nearly double the absorption magnitude of other samples.
- **Missing Values**: The missing value flags `-9999` and below detection limit flags `-8888` were parsed and successfully cleaned.

### Document Analysis
- **Cruise Discrepancy**: The laboratory spreadsheet `Sosik_14-31_report.xlsx` contains 194 records spanning 6 different cruises. The SeaBASS `.sb` HPLC file has been correctly filtered down to just the 32 records belonging to cruise `AE2426`.
- **Instrument Mismatch**: Although checklists for both Shimadzu and Perkin Elmer spectrophotometers were present, all 12 CDOM files were scanned using the `Shimadzu UV-2600i`.

### CDOM $\leftrightarrow$ HPLC Alignment
- **Matches**: We identified **11 Level-1 (Exact) matches** between the CDOM surface samples and the HPLC surface samples.
- **The Unmatched Sample**: One CDOM sample (`NES-LTER_AE2426_ag_202411090118_004m_R1.sb`) collected at 3.6m has **no corresponding HPLC match**.
- **Reason**: The only HPLC sample analyzed at that station on that day was collected at a depth of **24.6 meters**. The 21-meter depth discrepancy prevents alignment.

### ML & AIS Feasibility
- **Supervised ML**: **Unfeasible** due to the small matched sample size ($N=11$). Supervised regression models would suffer from severe overfitting.
- **Unsupervised ML & AIS**: **Feasible**. PCA successfully reduces the 551 wavelengths to 2 components. The Capstone's Negative Selection Algorithm can easily use these spectral features to run real-time OOD (Out-of-Distribution) optical anomaly detection.

### IoT Relevance
- **Multispectral Approximation**: HPLC requires laboratory separation and cannot be deployed in-situ. However, CDOM absorption can be approximated by integrating low-cost multispectral sensors (AS7341) with the ESP32 to measure key bands (412, 443 nm).

## 5. Recommended Next Action
We recommend establishing an **"Optical Sensing Branch"** for Phase 10 of the Capstone. This will include:
1. Simulating a virtual spectrophotometer on the ESP32.
2. Publishing spectral band telemetry via MQTT.
3. Incorporating a spectral AIS anomaly score into the Dempster-Shafer Evidence Fusion Engine to compute integrated water quality indexes.
