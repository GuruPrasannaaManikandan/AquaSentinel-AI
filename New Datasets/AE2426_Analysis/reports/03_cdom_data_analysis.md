# CDOM/ag Spectral Dataset Analysis

This report presents a forensic and scientific analysis of the Chromophoric Dissolved Organic Matter (CDOM) absorption coefficient ($a_g$) and absorbance spectral files.

## Summary of the CDOM Dataset
- **Total Files**: 12 SeaBASS spectral files (`.sb`)
- **Total Raw Measurements (rows)**: 6612 (551 spectral measurements per physical sample)
- **Independent Physical Water Samples**: 12 samples (each file represents a single physical water sample)
- **Spectral Coverage**: 300 nm to 850 nm with exactly 1 nm spacing
- **Wavelength Grids Uniformity**: Identical across all files (300 to 850 nm)
- **Combine Feasibility**: Highly feasible and recommended without interpolation. `cdom_wide.csv` has been generated.

## Metadata Summary
The following table summarizes the metadata extracted from each CDOM sample file:

| Filename | Date | Time (GMT) | Latitude | Longitude | Depth (m) | Instrument Model | Water Depth (m) |
|---|---|---|---|---|---|---|---|
| `NES-LTER_AE2426_ag_202411061634_003m_R1.sb` | 20241106 | 16:34:45 | 41.1959 | -70.8836 | 2.9 | UV-2600i_serial_no:A12595900733 | 23.0 |
| `NES-LTER_AE2426_ag_202411070844_003m_R1.sb` | 20241107 | 08:44:42 | 41.0317 | -70.8808 | 2.9 | UV-2600i_serial_no:A12595900733 | 46.0 |
| `NES-LTER_AE2426_ag_202411071321_004m_R1.sb` | 20241107 | 13:21:43 | 40.5140 | -70.8821 | 3.7 | UV-2600i_serial_no:A12595900733 | 77.0 |
| `NES-LTER_AE2426_ag_202411081114_003m_R1.sb` | 20241108 | 11:14:58 | 39.7694 | -70.8881 | 2.5 | UV-2600i_serial_no:A12595900733 | 1593.0 |
| `NES-LTER_AE2426_ag_202411081827_003m_R1.sb` | 20241108 | 18:27:33 | 39.9280 | -70.8643 | 3.1 | UV-2600i_serial_no:A12595900733 | 452.0 |
| `NES-LTER_AE2426_ag_202411090118_004m_R1.sb` | 20241109 | 01:18:19 | 40.0481 | -70.8842 | 3.6 | UV-2600i_serial_no:A12595900733 | 205.0 |
| `NES-LTER_AE2426_ag_202411100355_004m_R1.sb` | 20241110 | 03:55:32 | 40.2569 | -70.8834 | 3.8 | UV-2600i_serial_no:A12595900733 | 122.0 |
| `NES-LTER_AE2426_ag_202411100657_003m_R1.sb` | 20241110 | 06:57:57 | 40.1484 | -70.8941 | 3.3 | UV-2600i_serial_no:A12595900733 | 139.0 |
| `NES-LTER_AE2426_ag_202411100954_003m_R1.sb` | 20241110 | 09:54:18 | 40.3631 | -70.8821 | 2.7 | UV-2600i_serial_no:A12595900733 | 88.0 |
| `NES-LTER_AE2426_ag_202411101306_002m_R1.sb` | 20241110 | 13:06:09 | 40.7008 | -70.8845 | 2.5 | UV-2600i_serial_no:A12595900733 | 60.0 |
| `NES-LTER_AE2426_ag_202411110300_004m_R1.sb` | 20241111 | 03:00:02 | 41.0310 | -70.8832 | 4.3 | UV-2600i_serial_no:A12595900733 | 40.0 |
| `NES-LTER_AE2426_ag_202411110643_003m_R1.sb` | 20241111 | 06:43:59 | 41.3230 | -70.5496 | 3.3 | UV-2600i_serial_no:A12595900733 | 16.0 |

## Statistical Analysis of CDOM variables
- **$a_g$ (Absorption Coefficient, unit 1/m)**:
  - **Count**: 6612 values
  - **Min**: -0.076115
  - **Max**: 1.354744
  - **Mean**: 0.081820
  - **Median (50%)**: 0.009203
  - **Standard Deviation**: 0.185575
  - **Quartiles**: 25% = -0.000725, 75% = 0.071623

- **`abs_ag` (Absorbance, unitless)**:
  - **Count**: 6612 values
  - **Min**: -0.002856
  - **Max**: 0.059445
  - **Mean**: 0.004089
  - **Median (50%)**: 0.000953
  - **Standard Deviation**: 0.008087
  - **Quartiles**: 25% = 0.000403, 75% = 0.003666

## Data Quality Findings and Anomalies
1. **Negative Values**:
   - There are **1782** negative $a_g$ measurements and **1028** negative absorbance measurements.
   - *Scientific Interpretation*: Negative values represent measurement noise, baseline drift, or instrument fluctuations, particularly at longer wavelengths (>650 nm) where water absorption dominates and CDOM absorption is extremely close to zero. They should not be simply discarded but understood as statistical variations around zero.
2. **Missing and NaN Values**:
   - There are **0** NaN/missing values in the processed dataset.
   - The missing flag code `/missing=-9999` was resolved successfully.
3. **Outliers**:
   - Outlier checks (e.g., $a_g$ at 300 nm) show that sample `NES-LTER_AE2426_ag_202411110643_003m_R1.sb` has significantly higher absorption across all wavelengths compared to others (max $a_g$ of 1.3547 at 300 nm compared to other samples which range from 0.4 to 1.2 1/m). This is a potential outlier or a sample from a high-runoff coastal station.

## Pseudoreplication Warning
Treating all 6612 data rows as independent samples for Machine Learning is a severe case of **pseudoreplication**! The 551 wavelength rows in each file belong to **one** physical water sample. For any supervised ML or anomaly detection, there are only **12 independent physical samples**.

## Baseline Correction and Smoothing
Reviewing the metadata and comments, the files represent preliminary/final processed absorption scan data. Baseline subtraction (using purified Milli-Q water as reference) is standard practice and is confirmed in the scientific protocol.
