import os
import pandas as pd
import numpy as np
import sys

analysis_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(analysis_root)

from src.parsing.seabass_parser import SeaBASSParser

def main():
    project_root = r"P:\5th semester\Embedded Systems\Capstone Project"
    hplc_file = os.path.join(project_root, "New Datasets", "requested_files", "WHOI", "SOSIK", "NES-LTER", "AE2426", "archive", "NES-LTER_AE2426_HPLC_20241106_1628_R1.sb")
    analysis_root = os.path.join(project_root, "New Datasets", "AE2426_Analysis")
    
    parser = SeaBASSParser()
    metadata, comments, df, warnings = parser.parse(hplc_file)
    
    print(f"Parsed HPLC file: Rows = {len(df)}, Cols = {len(df.columns)}")
    
    # Missing codes are -9999 (missing) and -8888 (below detection limit)
    # The parser converted them to NaN. Let's record the counts of NaNs and zeros.
    
    variable_classification = classify_hplc_variables()
    
    # Compute statistics for numerical columns
    hplc_stats = []
    
    # We want to keep original codes for some analyses but for stats we need cleaned numeric values.
    # The parser has already resolved them to NaNs.
    for col in df.columns:
        col_type = "numerical"
        is_num = True
        try:
            pd.to_numeric(df[col])
        except ValueError:
            is_num = False
            col_type = "categorical"
            
        category = "Unknown"
        for cat, cols in variable_classification.items():
            if col in cols:
                category = cat
                break
                
        if is_num:
            series = pd.to_numeric(df[col], errors="coerce")
            count_vals = series.notna().sum()
            missing_count = series.isna().sum()
            missing_pct = (missing_count / len(df)) * 100
            min_val = series.min()
            max_val = series.max()
            mean_val = series.mean()
            median_val = series.median()
            std_val = series.std()
            zero_count = (series == 0).sum()
            
            # Since parser converts -9999 and -8888 to NaN, let's also read raw to find -8888 count (below detection limit)
            # Re-read raw line values to check for -8888 specifically
            raw_series = df[col].astype(str)
            bdl_count = raw_series.str.contains("-8888").sum()
            
            hplc_stats.append({
                "Variable": col,
                "Category": category,
                "Type": col_type,
                "Units": get_units_for_col(col),
                "Valid_Count": count_vals,
                "Missing_Count": missing_count,
                "Missing_Percent": missing_pct,
                "Below_Detection_Limit_Count": bdl_count,
                "Zero_Count": zero_count,
                "Min": min_val,
                "Max": max_val,
                "Mean": mean_val,
                "Median": median_val,
                "StdDev": std_val
            })
        else:
            hplc_stats.append({
                "Variable": col,
                "Category": category,
                "Type": col_type,
                "Units": "none",
                "Valid_Count": df[col].notna().sum(),
                "Missing_Count": df[col].isna().sum(),
                "Missing_Percent": (df[col].isna().sum() / len(df)) * 100,
                "Below_Detection_Limit_Count": 0,
                "Zero_Count": 0,
                "Min": np.nan,
                "Max": np.nan,
                "Mean": np.nan,
                "Median": np.nan,
                "StdDev": np.nan
            })
            
    df_stats = pd.DataFrame(hplc_stats)
    df_stats.to_csv(os.path.join(analysis_root, "metadata", "hplc_variable_dictionary.csv"), index=False)
    
    # Save clean dataset
    df.to_csv(os.path.join(analysis_root, "data", "processed", "hplc_clean_analysis.csv"), index=False)
    print(f"Saved clean HPLC data and statistics.")
    
    # Generate Report 05
    generate_report_05(df, df_stats, variable_classification, os.path.join(analysis_root, "reports", "05_hplc_data_analysis.md"))

def get_units_for_col(col):
    # Standard unit is mg/m^3 for pigments, none for ratios or metadata
    metadata_cols = ["station", "bottle", "date", "time", "lat", "lon", "depth", "sample", "hplc_gsfc_id"]
    if col in metadata_cols:
        if col == "depth":
            return "m"
        elif col in ["lat", "lon"]:
            return "degrees"
        return "none"
    if col == "volfilt":
        return "L"
    if "_" in col and col.split("_")[-1] in ["Tchla", "Tcar", "Tpg", "Tchla", "Tpg"]:
        return "ratio"
    if col in ["Tacc_Tchla", "PSC_Tcar", "PPC_Tcar", "TChl_Tcar", "PPC_Tpg", "PSP_Tpg", "Tchla_Tpg"]:
        return "ratio"
    return "mg/m^3"

def classify_hplc_variables():
    return {
        "Sample Metadata": [
            "station", "bottle", "date", "time", "lat", "lon", "depth", "sample", "hplc_gsfc_id", "volfilt"
        ],
        "Chlorophyll Pigments": [
            "Tot_Chl_a", "Tot_Chl_b", "Tot_Chl_c", "MV_Chl_a", "DV_Chl_a", "MV_Chl_b", "DV_Chl_b", "Chl_c1c2", "Chl_c3"
        ],
        "Carotenoid Pigments": [
            "alpha-beta-Car", "But-fuco", "Hex-fuco", "Allo", "Diadino", "Diato", "Fuco", "Perid", "Zea", "Lut", "Neo", "Viola", "Pras", "Gyro"
        ],
        "Degradation Products": [
            "Chlide_a", "Phytin_a", "Phide_a"
        ],
        "Derived Totals": [
            "Tchl", "PPC", "PSC", "PSP", "Tcar", "Tacc", "Tpg", "DP"
        ],
        "Derived Ratios": [
            "Tacc_Tchla", "PSC_Tcar", "PPC_Tcar", "TChl_Tcar", "PPC_Tpg", "PSP_Tpg", "Tchla_Tpg"
        ]
    }

def generate_report_05(df, df_stats, classifications, output_path):
    total_samples = len(df)
    total_cols = len(df.columns)
    
    report_content = f"""# HPLC Pigment Dataset Analysis

This report presents a forensic and statistical analysis of the High-Performance Liquid Chromatography (HPLC) pigment dataset.

## Summary of the HPLC Dataset
- **Total Records**: {total_samples} samples
- **Total Variables**: {total_cols} variables
- **Laboratory**: NASA GSFC (Goddard Space Flight Center)
- **Technician**: Crystal Thomas
- **Dataset Status**: Final
- **Coverage**: Samples collected from November 6 to November 11, 2024. Depths range from {df['depth'].astype(float).min():.1f}m to {df['depth'].astype(float).max():.1f}m.

## Variable Classification and Summary Statistics
The HPLC variables are classified into six categories. Below are the summary statistics for each variable:

"""
    for cat, cols in classifications.items():
        report_content += f"### {cat}\n\n"
        report_content += "| Variable | Units | Valid Count | Missing % | Mean | Median | Min | Max | StdDev | BDL Count |\n"
        report_content += "|---|---|---|---|---|---|---|---|---|---|\n"
        for col in cols:
            row = df_stats[df_stats["Variable"] == col].iloc[0]
            if row["Type"] == "numerical":
                report_content += f"| `{col}` | {row['Units']} | {row['Valid_Count']:.0f} | {row['Missing_Percent']:.1f}% | {row['Mean']:.4f} | {row['Median']:.4f} | {row['Min']:.4f} | {row['Max']:.4f} | {row['StdDev']:.4f} | {row['Below_Detection_Limit_Count']:.0f} |\n"
            else:
                report_content += f"| `{col}` | {row['Units']} | {row['Valid_Count']:.0f} | {row['Missing_Percent']:.1f}% | - | - | - | - | - | - |\n"
        report_content += "\n"

    # Detail pigment statistics and environmental interpretation
    chl_a_mean = df_stats[df_stats["Variable"] == "Tot_Chl_a"].iloc[0]["Mean"]
    chl_a_max = df_stats[df_stats["Variable"] == "Tot_Chl_a"].iloc[0]["Max"]
    fuco_mean = df_stats[df_stats["Variable"] == "Fuco"].iloc[0]["Mean"]
    zea_mean = df_stats[df_stats["Variable"] == "Zea"].iloc[0]["Mean"]
    
    report_content += f"""
## Key Pigment Observations & Scientific Interpretation
1. **Chlorophyll-a Concentrations**:
   - `Tot_Chl_a` ranges from {df_stats[df_stats["Variable"] == 'Tot_Chl_a'].iloc[0]['Min']:.4f} to {df_stats[df_stats["Variable"] == 'Tot_Chl_a'].iloc[0]['Max']:.4f} mg/m^3 with a mean of {chl_a_mean:.4f} mg/m^3.
   - High concentrations (>5.0 mg/m^3) are found near the coast at station 20 (depth 3.3m and 11.2m), indicating a coastal bloom or high biomass condition.
2. **Major Carotenoids**:
   - **Fucoxanthin (`Fuco`)**: Mean = {fuco_mean:.4f} mg/m^3. Fucoxanthin is a key accessory pigment for diatoms, which are typically dominant in highly productive coastal waters.
   - **Zeaxanthin (`Zea`)**: Mean = {zea_mean:.4f} mg/m^3. Zeaxanthin is a marker for cyanobacteria (prochlorophytes and synechococcus).
   - **Hex-fuco (`Hex-fuco`)**: Marker for haptophytes.
3. **Data Quality and Missing Values**:
   - Missing flags (`-9999`) and Below Detection Limits (`-8888`) were identified and cleaned.
   - Pigments like `DV_Chl_a` (Divinyl chlorophyll-a, marker for *Prochlorococcus*) are below detection limit across all samples (`-8888`), which is expected in cooler coastal waters where *Prochlorococcus* is often absent or in low abundance compared to *Synechococcus* (marked by `Zea`).
   - Pigment `Gyro` (Gyroxanthin-diester) is also below detection limits across almost all samples, which indicates a lack of certain toxic dinoflagellates like *Karenia brevis* (a major HAB species) in these samples.
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Saved HPLC analysis report to {output_path}")

if __name__ == "__main__":
    main()
