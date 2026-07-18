# Report 02: Documentation Extraction and Analysis

This report documents the scientific methodology, instrument parameters, and quality-control standards extracted from the documentation archive (`documents.tgz`).

## Documents Analyzed

### 1. CDOM Spectrophotometer Checklist: Shimadzu UV-2600i
- **Purpose**: Checklist for the spectrophotometer used to scan the CDOM samples.
- **Instrument**: Shimadzu UV-2600i spectrophotometer (Serial No. A12595900733) with an integrating sphere.
- **Methodology**: Dissolved organic matter absorption is measured on filtrate after passing raw water through 0.2 $\mu$m filters. Purified Milli-Q water is used as the baseline reference in a matched quartz cell.
- **QC**: Instrument noise is checked (standard deviation of blank < 0.0005 absorbance units), and baseline stability is monitored.
- **Relevance**: Documented evidence that all 12 CDOM files were processed using this instrument.

### 2. CDOM Spectrophotometer Checklist: Perkin Elmer Lambda 650 S
- **Purpose**: Instrument checklist for an alternate laboratory spectrophotometer.
- **Instrument**: Perkin Elmer Lambda 650 S.
- **Relevance**: None of the 12 CDOM files in the AE2426 dataset were scanned with this instrument. However, it indicates the laboratory maintains multiple instruments for inter-comparison.

### 3. CDOM Measurement Protocol (`NESLTER_CDOM_spec_protocol.pdf`)
- **Purpose**: Detailed step-by-step protocol for CDOM sample collection, storage, and scanning.
- **Methodology**: 
  - Samples are collected in pre-combusted amber glass bottles to prevent photo-degradation.
  - Filtration is performed using 0.2 $\mu$m membrane filters under low vacuum (< 5 in Hg) to prevent cell lysis (which would leak pigments and corrupt CDOM absorption).
  - Scanning is performed in a 10 cm quartz cuvette (pathlength $L = 0.1$ m) against a Milli-Q water blank.
  - Absorption coefficient $a_g$ ($m^{-1}$) is calculated from absorbance $A$ (unitless) using:
    $$a_g(\lambda) = \frac{2.303 \cdot A(\lambda)}{L}$$
- **Relevance**: Provides the physical equation relating `abs_ag` and `ag` in the 12 CDOM files.

### 4. HPLC Checklist (`checklist_hplc_AE2426.rtf`)
- **Purpose**: HPLC method summary and quality control checklist.
- **Methodology**: 
  - **Sample Collection**: Water is filtered onto 25 mm GF/F filters (nominal pore size 0.7 $\mu$m).
  - **Storage**: Filters are folded, placed in aluminum foil, and immediately frozen in liquid nitrogen.
  - **Extraction**: Pigments are extracted using 100% acetone, disrupted using a sonic probe for 12 seconds, and clarified through a 0.2 $\mu$m filter.
  - **Chromatography**: Separation is done using a reverse-phase column.
- **Calibration**: Calibrated using pigment standards from DHI Water and Environment (Horsholm, Denmark). Accuracy is monitored daily using Chlorophyll-a standards.
- **Resolutions**: Zeaxanthin and Lutein (`ZEA/LUT`) represent a critical pair with a chromatographic resolution $R_s = 1.0$.
- **Relevance**: Explains how the 51 variables in the HPLC file were quantified, confirming their high reliability (NASA GSFC laboratory processing).

### 5. GSFC Laboratory Spreadsheet (`Sosik_14-31_report.xlsx`)
- **Purpose**: Master laboratory Excel report from NASA's Goddard Space Flight Center.
- **Contents**: Raw peak areas, LOQ (Limit of Quantitation) tables, and replicate filter precision metrics across 194 samples.
- **Relevance**: Revealed that the 32 HPLC samples in the `.sb` file were extracted from a master list containing 6 cruises (EN712, EN715, EN720, AE2426, EN727, AR88). It documents comments on labeling mistakes and foil repacking, ensuring full data lineage.

### 6. HPLC Method Summary (`HPLC_method_summary_SeaBASS_updated01122026.doc`)
- **Purpose**: Summarizes GSFC's HPLC chromatographic method, including solvent gradients and formulas for derived pigment groups (e.g. Total Chlorophyll `Tchl`, Photoprotective Carotenoids `PPC`).
- **Relevance**: Validates the equations used to compute derived sums like `Tpg` and `DP` in the HPLC file.

---

## Relevance to Capstone Project
- **CDOM**: The protocol confirms that CDOM represents dissolved organic matter. This provides a completely different ecological indicator than the physical/chemical sensors currently simulated.
- **HPLC**: Pigments represent the laboratory "gold standard" ground truth. The checklists show that HPLC cannot be deployed as an IoT sensor because of the manual preparation and liquid nitrogen freezing steps, validating our architectural split between IoT optical telemetry and laboratory-based model calibration.
