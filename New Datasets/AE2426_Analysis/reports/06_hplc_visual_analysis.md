# HPLC Scientific Visualization Report

This report presents and analyzes the scientific visualizations generated from the AE2426 HPLC pigment dataset.

## Visualizations List

### 1. Concentration Distributions of Major Pigments (Boxplot)
![Pigment Concentration Distributions](file:///P:/5th semester/Embedded Systems/Capstone Project/New Datasets/AE2426_Analysis/figures/hplc/hplc_pigment_boxplot.png)
- **Observations**:
  - The boxplot uses a logarithmic scale to show concentrations spanning three orders of magnitude.
  - `Tot_Chl_a` is the most abundant pigment, peaking at >6.0 mg/m^3.
  - `Fuco` (Fucoxanthin, marker for diatoms) is also highly abundant, indicating that diatoms represent a major component of the phytoplankton biomass.
  - `Zea` (Zeaxanthin, marker for cyanobacteria/synechococcus) has a much lower concentration (around 0.02 - 0.05 mg/m^3), reflecting that prokaryotic picophytoplankton represent a smaller fraction of the biomass in this nutrient-rich fall dataset.
  - Accessory pigments like `Tot_Chl_b`, `Hex-fuco`, and `Allo` are intermediate.

### 2. Fucoxanthin vs Total Chlorophyll a (Scatter Plot)
![Fucoxanthin vs Total Chlorophyll a](file:///P:/5th semester/Embedded Systems/Capstone Project/New Datasets/AE2426_Analysis/figures/hplc/hplc_fuco_vs_chla.png)
- **Observations**:
  - There is a very strong, tight linear relationship between Fucoxanthin (`Fuco`) and Total Chlorophyll-a (`Tot_Chl_a`).
  - This indicates that changes in total phytoplankton biomass are primarily driven by diatom biomass variations.
  - Points are colored by depth, showing that higher concentrations (both Chl-a and Fucoxanthin) are concentrated in shallower surface waters.

### 3. Depth Profile of Total Chlorophyll a
![Depth Profile of Chlorophyll a](file:///P:/5th semester/Embedded Systems/Capstone Project/New Datasets/AE2426_Analysis/figures/hplc/hplc_depth_profile_chla.png)
- **Observations**:
  - This vertical profile shows higher Chlorophyll-a concentrations at shallower depths (surface down to 20m), with a distinct drop-off at deeper stations (>30m).
  - Surface samples reach up to 6.78 mg/m^3, while deep samples at 50-65m remain below 0.5 mg/m^3. This is consistent with light limitation in deep marine waters.

### 4. Correlation Heatmap of Key Pigments
![Pigment Correlation Matrix](file:///P:/5th semester/Embedded Systems/Capstone Project/New Datasets/AE2426_Analysis/figures/hplc/hplc_pigment_correlation.png)
- **Observations**:
  - `Tot_Chl_a` is extremely highly correlated with `Fuco` (r = 0.93) and `Tot_Chl_c` (r = 0.99), suggesting a co-presence of diatoms and associated chlorophylls.
  - `Zea` has moderate correlation with Chl-a (r = 0.49), indicating that cyanobacteria do not follow the exact same distribution as diatoms, possibly preferring different depths or spatial niches.
  - `volfilt` (volume filtered in liters) has zero correlation with pigment concentrations, confirming that the sample preparation did not introduce artificial concentration biases.

### 5. Spatial Distribution of Chlorophyll a
![Spatial Distribution of Chlorophyll a](file:///P:/5th semester/Embedded Systems/Capstone Project/New Datasets/AE2426_Analysis/figures/hplc/hplc_spatial_chlorophyll.png)
- **Observations**:
  - Highlights a strong geographical gradient: Chlorophyll-a is highest at the coastal stations (Station 20, north, near-shore, reaching >6.0 mg/m^3) and drops significantly at offshore stations (Station 10, south, outer-shelf, dropping to <0.5 mg/m^3).
  - This matches typical oceanographic patterns where nearshore waters are enriched with nutrients (promoting large diatom blooms), while offshore waters are more oligotrophic.
