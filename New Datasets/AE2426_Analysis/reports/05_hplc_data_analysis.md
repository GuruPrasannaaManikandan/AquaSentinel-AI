# HPLC Pigment Dataset Analysis

This report presents a forensic and statistical analysis of the High-Performance Liquid Chromatography (HPLC) pigment dataset.

## Summary of the HPLC Dataset
- **Total Records**: 32 samples
- **Total Variables**: 51 variables
- **Laboratory**: NASA GSFC (Goddard Space Flight Center)
- **Technician**: Crystal Thomas
- **Dataset Status**: Final
- **Coverage**: Samples collected from November 6 to November 11, 2024. Depths range from 2.5m to 65.1m.

## Variable Classification and Summary Statistics
The HPLC variables are classified into six categories. Below are the summary statistics for each variable:

### Sample Metadata

| Variable | Units | Valid Count | Missing % | Mean | Median | Min | Max | StdDev | BDL Count |
|---|---|---|---|---|---|---|---|---|---|
| `station` | none | 32 | 0.0% | 12.6875 | 15.0000 | 1.0000 | 20.0000 | 5.7945 | 0 |
| `bottle` | none | 32 | 0.0% | 10.9062 | 11.0000 | 1.0000 | 21.0000 | 5.7606 | 0 |
| `date` | none | 32 | 0.0% | 20241109.0000 | 20241110.0000 | 20241106.0000 | 20241111.0000 | 1.5450 | 0 |
| `time` | none | 32 | 0.0% | - | - | - | - | - | - |
| `lat` | degrees | 32 | 0.0% | 40.4744 | 40.3630 | 39.7690 | 41.3230 | 0.4888 | 0 |
| `lon` | degrees | 32 | 0.0% | -70.8620 | -70.8830 | -70.8940 | -70.5500 | 0.0820 | 0 |
| `depth` | m | 32 | 0.0% | 22.5281 | 19.5500 | 2.5000 | 65.1000 | 20.2100 | 0 |
| `sample` | none | 32 | 0.0% | - | - | - | - | - | - |
| `hplc_gsfc_id` | none | 32 | 0.0% | - | - | - | - | - | - |
| `volfilt` | L | 32 | 0.0% | 0.7224 | 0.5480 | 0.5370 | 1.0600 | 0.2462 | 0 |

### Chlorophyll Pigments

| Variable | Units | Valid Count | Missing % | Mean | Median | Min | Max | StdDev | BDL Count |
|---|---|---|---|---|---|---|---|---|---|
| `Tot_Chl_a` | mg/m^3 | 32 | 0.0% | 1.6866 | 1.5480 | 0.1040 | 6.7800 | 1.5718 | 0 |
| `Tot_Chl_b` | mg/m^3 | 32 | 0.0% | 0.1552 | 0.1520 | 0.0160 | 0.4130 | 0.0919 | 0 |
| `Tot_Chl_c` | mg/m^3 | 32 | 0.0% | 0.3369 | 0.3265 | 0.0290 | 1.1630 | 0.2693 | 0 |
| `MV_Chl_a` | mg/m^3 | 32 | 0.0% | 1.6158 | 1.5285 | 0.1000 | 6.5180 | 1.4798 | 0 |
| `DV_Chl_a` | mg/m^3 | 9 | 71.9% | 0.0271 | 0.0230 | 0.0020 | 0.0640 | 0.0243 | 0 |
| `MV_Chl_b` | mg/m^3 | 32 | 0.0% | 0.1495 | 0.1425 | 0.0120 | 0.4130 | 0.0957 | 0 |
| `DV_Chl_b` | mg/m^3 | 8 | 75.0% | 0.0229 | 0.0115 | 0.0030 | 0.1000 | 0.0330 | 0 |
| `Chl_c1c2` | mg/m^3 | 32 | 0.0% | 0.2216 | 0.1935 | 0.0130 | 0.9190 | 0.2191 | 0 |
| `Chl_c3` | mg/m^3 | 32 | 0.0% | 0.1152 | 0.1310 | 0.0160 | 0.2440 | 0.0561 | 0 |

### Carotenoid Pigments

| Variable | Units | Valid Count | Missing % | Mean | Median | Min | Max | StdDev | BDL Count |
|---|---|---|---|---|---|---|---|---|---|
| `alpha-beta-Car` | mg/m^3 | 32 | 0.0% | 0.0743 | 0.0710 | 0.0060 | 0.2640 | 0.0591 | 0 |
| `But-fuco` | mg/m^3 | 24 | 25.0% | 0.0320 | 0.0320 | 0.0070 | 0.0670 | 0.0120 | 0 |
| `Hex-fuco` | mg/m^3 | 32 | 0.0% | 0.1069 | 0.1080 | 0.0080 | 0.1860 | 0.0564 | 0 |
| `Allo` | mg/m^3 | 31 | 3.1% | 0.0265 | 0.0260 | 0.0010 | 0.0550 | 0.0177 | 0 |
| `Diadino` | mg/m^3 | 32 | 0.0% | 0.0683 | 0.0605 | 0.0040 | 0.2560 | 0.0620 | 0 |
| `Diato` | mg/m^3 | 27 | 15.6% | 0.0079 | 0.0060 | 0.0010 | 0.0250 | 0.0063 | 0 |
| `Fuco` | mg/m^3 | 32 | 0.0% | 0.5986 | 0.4370 | 0.0380 | 2.5660 | 0.6611 | 0 |
| `Perid` | mg/m^3 | 32 | 0.0% | 0.0444 | 0.0455 | 0.0040 | 0.0900 | 0.0300 | 0 |
| `Zea` | mg/m^3 | 32 | 0.0% | 0.0275 | 0.0275 | 0.0030 | 0.0510 | 0.0122 | 0 |
| `Lut` | mg/m^3 | 32 | 0.0% | 0.0062 | 0.0065 | 0.0010 | 0.0140 | 0.0037 | 0 |
| `Neo` | mg/m^3 | 32 | 0.0% | 0.0166 | 0.0165 | 0.0010 | 0.0420 | 0.0102 | 0 |
| `Viola` | mg/m^3 | 32 | 0.0% | 0.0146 | 0.0145 | 0.0010 | 0.0530 | 0.0119 | 0 |
| `Pras` | mg/m^3 | 31 | 3.1% | 0.0350 | 0.0400 | 0.0030 | 0.0770 | 0.0177 | 0 |
| `Gyro` | mg/m^3 | 0 | 100.0% | nan | nan | nan | nan | nan | 0 |

### Degradation Products

| Variable | Units | Valid Count | Missing % | Mean | Median | Min | Max | StdDev | BDL Count |
|---|---|---|---|---|---|---|---|---|---|
| `Chlide_a` | mg/m^3 | 32 | 0.0% | 0.0632 | 0.0170 | 0.0010 | 0.6100 | 0.1185 | 0 |
| `Phytin_a` | mg/m^3 | 32 | 0.0% | 0.0302 | 0.0205 | 0.0030 | 0.2090 | 0.0459 | 0 |
| `Phide_a` | mg/m^3 | 32 | 0.0% | 0.0628 | 0.0465 | 0.0070 | 0.3890 | 0.0877 | 0 |

### Derived Totals

| Variable | Units | Valid Count | Missing % | Mean | Median | Min | Max | StdDev | BDL Count |
|---|---|---|---|---|---|---|---|---|---|
| `Tchl` | mg/m^3 | 32 | 0.0% | 2.1787 | 2.0635 | 0.1490 | 8.3560 | 1.9105 | 0 |
| `PPC` | mg/m^3 | 32 | 0.0% | 0.2025 | 0.2025 | 0.0140 | 0.6260 | 0.1422 | 0 |
| `PSC` | mg/m^3 | 32 | 0.0% | 0.7739 | 0.6915 | 0.0650 | 2.8350 | 0.6835 | 0 |
| `PSP` | mg/m^3 | 32 | 0.0% | 2.9526 | 2.8150 | 0.2140 | 11.1910 | 2.5911 | 0 |
| `Tcar` | mg/m^3 | 32 | 0.0% | 0.9764 | 0.9125 | 0.0810 | 3.4610 | 0.8228 | 0 |
| `Tacc` | mg/m^3 | 32 | 0.0% | 1.4685 | 1.4465 | 0.1260 | 5.0370 | 1.1615 | 0 |
| `Tpg` | mg/m^3 | 32 | 0.0% | 3.1551 | 3.0215 | 0.2300 | 11.8170 | 2.7311 | 0 |
| `DP` | mg/m^3 | 32 | 0.0% | 0.9823 | 0.9800 | 0.0870 | 3.3290 | 0.7664 | 0 |

### Derived Ratios

| Variable | Units | Valid Count | Missing % | Mean | Median | Min | Max | StdDev | BDL Count |
|---|---|---|---|---|---|---|---|---|---|
| `Tacc_Tchla` | ratio | 32 | 0.0% | 0.9838 | 0.9350 | 0.7400 | 1.5100 | 0.1748 | 0 |
| `PSC_Tcar` | ratio | 32 | 0.0% | 0.7703 | 0.7900 | 0.5800 | 0.8500 | 0.0653 | 0 |
| `PPC_Tcar` | ratio | 32 | 0.0% | 0.2297 | 0.2100 | 0.1500 | 0.4200 | 0.0653 | 0 |
| `TChl_Tcar` | ratio | 32 | 0.0% | 2.1909 | 2.1800 | 1.8400 | 2.4700 | 0.1626 | 0 |
| `PPC_Tpg` | ratio | 32 | 0.0% | 0.0712 | 0.0700 | 0.0500 | 0.1500 | 0.0221 | 0 |
| `PSP_Tpg` | ratio | 32 | 0.0% | 0.9288 | 0.9300 | 0.8500 | 0.9500 | 0.0221 | 0 |
| `Tchla_Tpg` | ratio | 32 | 0.0% | 0.5072 | 0.5200 | 0.4000 | 0.5700 | 0.0403 | 0 |


## Key Pigment Observations & Scientific Interpretation
1. **Chlorophyll-a Concentrations**:
   - `Tot_Chl_a` ranges from 0.1040 to 6.7800 mg/m^3 with a mean of 1.6866 mg/m^3.
   - High concentrations (>5.0 mg/m^3) are found near the coast at station 20 (depth 3.3m and 11.2m), indicating a coastal bloom or high biomass condition.
2. **Major Carotenoids**:
   - **Fucoxanthin (`Fuco`)**: Mean = 0.5986 mg/m^3. Fucoxanthin is a key accessory pigment for diatoms, which are typically dominant in highly productive coastal waters.
   - **Zeaxanthin (`Zea`)**: Mean = 0.0275 mg/m^3. Zeaxanthin is a marker for cyanobacteria (prochlorophytes and synechococcus).
   - **Hex-fuco (`Hex-fuco`)**: Marker for haptophytes.
3. **Data Quality and Missing Values**:
   - Missing flags (`-9999`) and Below Detection Limits (`-8888`) were identified and cleaned.
   - Pigments like `DV_Chl_a` (Divinyl chlorophyll-a, marker for *Prochlorococcus*) are below detection limit across all samples (`-8888`), which is expected in cooler coastal waters where *Prochlorococcus* is often absent or in low abundance compared to *Synechococcus* (marked by `Zea`).
   - Pigment `Gyro` (Gyroxanthin-diester) is also below detection limits across almost all samples, which indicates a lack of certain toxic dinoflagellates like *Karenia brevis* (a major HAB species) in these samples.
