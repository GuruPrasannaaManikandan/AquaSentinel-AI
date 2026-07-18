# Report 10: Scientific Limitations and Claims Audit

This report outlines the scientific constraints and limitations of the AE2426 dataset, highlighting the risks of making overextended claims.

## Key Scientific Limitations

### 1. Small Sample Size
- **The Core Constraint**: There are only **12 physical CDOM samples** and **32 HPLC samples**, resulting in only **11 matched spatio-temporal pairs**.
- **Impact**: Any supervised ML model trained on 11 samples will overfit and fail to generalize. No valid predictions of pigment concentrations from CDOM spectra can be developed using this dataset alone.

### 2. Spatial Restrictions
- **The Core Constraint**: All samples were collected from a single cruise (AE2426) along a cross-shelf transect of the North East Shelf (NES) between latitudes 39.7°N and 41.3°N, and longitudes -70.5°W and -70.9°W.
- **Impact**: The optical and chemical relationships identified here are specific to this shelf region. They cannot be generalized to other marine environments (e.g., oligotrophic open ocean, tropical coral reefs) or freshwater lakes (e.g., the CAML model workspace).

### 3. Temporal Restrictions
- **The Core Constraint**: Sampling took place over a 5-day period in the late fall (November 6 to 11, 2024).
- **Impact**: The dataset represents a specific fall condition (fall transition, nutrient mixing). The biological communities and CDOM concentrations are highly seasonal and cannot represent spring bloom or summer stratified conditions.

### 4. Laboratory Measurement Noise
- **The Core Constraint**: Spectrophotometric measurements at longer wavelengths (>650 nm) are highly sensitive to temperature fluctuations and instrument drift.
- **Impact**: This is evident in the negative $a_g$ and absorbance values recorded at wavelengths between 700 and 850 nm (representing measurement noise). Baseline drift correction is required before any spectral analysis in the red and near-infrared bands.

### 5. Lack of Direct Bloom Labels
- **The Core Constraint**: The dataset does not contain binary or categorical labels indicating "Bloom" or "No Bloom", nor does it identify toxic species (such as *Karenia brevis* or *Pseudo-nitzschia*).
- **Impact**: Any "bloom detection" or "ecosystem health" classifications must rely on arbitrary thresholding of Chlorophyll-a (e.g., Chl-a > 3.0 mg/m^3), which lacks official ecological validation.

### 6. HPLC $\leftrightarrow$ CDOM Spatio-Temporal Misalignment
- **The Core Constraint**: Water samples for CDOM and HPLC are collected from Niskin bottles on a CTD rosette. Though collected on the same cast, they are processed separately.
- **Impact**: At Station 12, a CDOM surface sample was taken (3.6m), but no corresponding surface HPLC sample was analyzed (HPLC was only analyzed at 24.6m). This depth mismatch resulted in one unmatched CDOM sample, reducing our co-analysis sample size.

### 7. Severe Pseudoreplication Hazard
- **The Core Constraint**: Each CDOM file contains 551 rows of wavelength measurements.
- **Impact**: Treating these 551 rows as independent samples for supervised learning artificially inflates the dataset size to 6,612 samples, leading to a false sense of model confidence. Wavelengths are highly collinear and belong to the same physical volume of water. They represent a single independent observation ($N=1$).

### 8. Validation Strategy Constraints
- **The Core Constraint**: Random splitting of data points will cause data leakage if wavelength rows from the same file are split between train and test sets.
- **Impact**: Group-based cross-validation (keeping entire files together) is mandatory.

---

## Claims Audit

To maintain scientific integrity, the project team must **avoid** making the following claims:
- **Do not claim** that the dataset can be used to train an ML model to detect algal blooms in real-time.
- **Do not claim** that CDOM spectra can reliably predict specific accessory pigments in-situ with this small sample size.
- **Do not claim** that these optical proxies are suitable for freshwater applications (CAML).
- **Do not claim** that negative absorption coefficients at longer wavelengths are biological signals (they are instrument noise).
