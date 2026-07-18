# CDOM Scientific Visualization Report

This report presents and analyzes the scientific visualizations generated from the AE2426 CDOM dataset.

## Visualizations List

### 1. CDOM Absorption Coefficient ($a_g$) Overlaid
![CDOM Absorption Coefficient Spectra Overlaid](file:///P:/5th semester/Embedded Systems/Capstone Project/New Datasets/AE2426_Analysis/figures/cdom/cdom_ag_overlaid.png)
- **Observations**: 
  - Standard exponential decay curves characteristic of CDOM absorption. Absorption is highest in the UV range (300 nm) and decays exponentially toward the near-infrared.
  - The sample `NES-LTER_AE2426_ag_202411110643_003m_R1.sb` (shown in red) stands out as an outlier with a starting $a_g$ of ~1.35 1/m at 300 nm, which is nearly double the typical value of other samples.
  - At wavelengths >650 nm, the absorption coefficient converges to values close to zero. Some files exhibit noise resulting in slight negative values at longer wavelengths.

### 2. CDOM Absorbance (`abs_ag`) Overlaid
![CDOM Absorbance Spectra Overlaid](file:///P:/5th semester/Embedded Systems/Capstone Project/New Datasets/AE2426_Analysis/figures/cdom/cdom_abs_overlaid.png)
- **Observations**:
  - Shows raw spectrophotometer absorbance readings, which match the exponential decay shape of the absorption coefficient.
  - Outlier sample again stands out significantly, reaching an absorbance value of ~0.06 at 300 nm.

### 3. CDOM Mean Spectral Profile and Variability
![CDOM Mean Spectral Profile and Variability](file:///P:/5th semester/Embedded Systems/Capstone Project/New Datasets/AE2426_Analysis/figures/cdom/cdom_ag_mean_variability.png)
- **Observations**:
  - The shaded band represents $\pm 1$ Standard Deviation.
  - The standard deviation is highest at shorter wavelengths (300 nm to 400 nm), reflecting spatial and temporal variability in water sample compositions. It decreases as the wavelength increases.

### 4. Depth Distribution of CDOM Samples
![Depth Distribution of CDOM Samples](file:///P:/5th semester/Embedded Systems/Capstone Project/New Datasets/AE2426_Analysis/figures/cdom/cdom_depth_distribution.png)
- **Observations**:
  - The sampling is concentrated in shallow surface waters, with depths between 2.5m and 4.3m. There are no deep-water samples in this CDOM set.

### 5. Spatial Sampling Map
![Spatial Sampling Map](file:///P:/5th semester/Embedded Systems/Capstone Project/New Datasets/AE2426_Analysis/figures/cdom/cdom_spatial_map.png)
- **Observations**:
  - Samples are distributed geographically across the inner shelf of the North East Shelf (NES).
  - Most CDOM sampling stations are clustered around a longitudinal transect of -70.88° East, stretching from 39.7° to 41.3° North, representing a cross-shelf transect.

### 6. Sampling Timeline
![Sampling Timeline](file:///P:/5th semester/Embedded Systems/Capstone Project/New Datasets/AE2426_Analysis/figures/cdom/cdom_sampling_timeline.png)
- **Observations**:
  - Samples were collected sequentially over a 5-day period from November 6 to November 11, 2024.
  - Sampling occurred at different hours of the day (some early morning, some mid-day, some night).
