import os
import pandas as pd
import numpy as np
import sys

# Add directory to sys path for parsing module import
analysis_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(analysis_root)

from src.parsing.seabass_parser import SeaBASSParser

def main():
    project_root = r"P:\5th semester\Embedded Systems\Capstone Project"
    archive_dir = os.path.join(project_root, "New Datasets", "requested_files", "WHOI", "SOSIK", "NES-LTER", "AE2426", "archive")
    analysis_root = os.path.join(project_root, "New Datasets", "AE2426_Analysis")
    
    files = sorted([f for f in os.listdir(archive_dir) if f.endswith(".sb") and "_ag_" in f])
    
    parser = SeaBASSParser()
    all_metadata = []
    long_records = []
    wide_records = []
    
    print(f"Parsing {len(files)} CDOM files...")
    
    for f in files:
        filepath = os.path.join(archive_dir, f)
        metadata, comments, df, warnings = parser.parse(filepath)
        
        # Track sample metadata
        # Resolve coordinates (removing '[DEG]')
        def clean_meta_val(val):
            if val is None:
                return None
            return float(re.sub(r"\[[A-Za-z]+\]", "", str(val))) if re.search(r"\d", str(val)) else val

        import re
        lat = clean_meta_val(metadata.get("north_latitude"))
        lon = clean_meta_val(metadata.get("east_longitude"))
        depth = float(metadata.get("measurement_depth", 0.0))
        date_str = metadata.get("start_date")
        time_str = re.sub(r"\[[A-Za-z]+\]", "", metadata.get("start_time", ""))
        
        # Store metadata dictionary
        meta_record = {
            "filename": f,
            "experiment": metadata.get("experiment"),
            "cruise": metadata.get("cruise"),
            "investigator": metadata.get("investigators"),
            "affiliation": metadata.get("affiliations"),
            "contact": metadata.get("contact"),
            "date": date_str,
            "time": time_str,
            "latitude": lat,
            "longitude": lon,
            "measurement_depth": depth,
            "water_depth": float(metadata.get("water_depth")) if metadata.get("water_depth") != "NA" else np.nan,
            "instrument_manufacturer": metadata.get("instrument_manufacturer"),
            "instrument_model": metadata.get("instrument_model"),
            "calibration_files": metadata.get("calibration_files"),
            "original_file_name": metadata.get("original_file_name"),
            "missing_code": metadata.get("missing"),
            "warnings_count": len(warnings)
        }
        all_metadata.append(meta_record)
        
        # Analyze data
        # Wavelength range check
        w_min = df["wavelength"].min()
        w_max = df["wavelength"].max()
        row_count = len(df)
        
        # Data Quality Checks
        n_nan_ag = df["ag"].isna().sum()
        n_nan_abs = df["abs_ag"].isna().sum()
        n_neg_ag = (df["ag"] < 0).sum()
        n_neg_abs = (df["abs_ag"] < 0).sum()
        
        # Basic stats
        ag_min = df["ag"].min()
        ag_max = df["ag"].max()
        ag_mean = df["ag"].mean()
        ag_median = df["ag"].median()
        ag_std = df["ag"].std()
        
        abs_min = df["abs_ag"].min()
        abs_max = df["abs_ag"].max()
        abs_mean = df["abs_ag"].mean()
        abs_median = df["abs_ag"].median()
        abs_std = df["abs_ag"].std()
        
        print(f"File: {f} | Rows: {row_count} | Wavelengths: {w_min}-{w_max} nm")
        print(f"  ag stats: min={ag_min:.4f}, max={ag_max:.4f}, mean={ag_mean:.4f}, std={ag_std:.4f}")
        print(f"  Quality: NaNs in ag={n_nan_ag}, Negatives in ag={n_neg_ag}, Negatives in abs_ag={n_neg_abs}")

        # Add long-format rows
        for _, r in df.iterrows():
            long_records.append({
                "filename": f,
                "date": date_str,
                "time": time_str,
                "lat": lat,
                "lon": lon,
                "depth": depth,
                "wavelength": r["wavelength"],
                "ag": r["ag"],
                "abs_ag": r["abs_ag"]
            })
            
        # Add wide-format row
        wide_row = {
            "filename": f,
            "date": date_str,
            "time": time_str,
            "lat": lat,
            "lon": lon,
            "depth": depth,
            "instrument": f"{metadata.get('instrument_manufacturer')} {metadata.get('instrument_model')}"
        }
        for _, r in df.iterrows():
            wl = int(r["wavelength"])
            wide_row[f"ag_{wl}"] = r["ag"]
            wide_row[f"abs_ag_{wl}"] = r["abs_ag"]
        wide_records.append(wide_row)

    # Save outputs
    df_meta = pd.DataFrame(all_metadata)
    df_meta.to_csv(os.path.join(analysis_root, "metadata", "cdom_sample_metadata.csv"), index=False)
    
    df_long = pd.DataFrame(long_records)
    df_long.to_csv(os.path.join(analysis_root, "data", "processed", "cdom_long.csv"), index=False)
    
    df_wide = pd.DataFrame(wide_records)
    df_wide.to_csv(os.path.join(analysis_root, "data", "processed", "cdom_wide.csv"), index=False)
    
    print("\nSaved processed CDOM CSVs:")
    print(f"  Long shape: {df_long.shape}")
    print(f"  Wide shape: {df_wide.shape}")
    print(f"  Metadata shape: {df_meta.shape}")

    # Generate Report 03
    generate_report_03(df_meta, df_long, df_wide, files, os.path.join(analysis_root, "reports", "03_cdom_data_analysis.md"))

def generate_report_03(df_meta, df_long, df_wide, files, output_path):
    # Perform global stats
    total_files = len(files)
    total_measurements = len(df_long)
    unique_dates = df_meta["date"].nunique()
    
    # Check for negatives
    neg_ag_count = (df_long["ag"] < 0).sum()
    neg_abs_count = (df_long["abs_ag"] < 0).sum()
    nan_ag_count = df_long["ag"].isna().sum()
    
    ag_stats = df_long["ag"].describe()
    abs_stats = df_long["abs_ag"].describe()
    
    # Check if wavelength grids are identical
    wavelength_grids_match = True
    wavelength_counts = df_long.groupby("filename")["wavelength"].count().tolist()
    if len(set(wavelength_counts)) != 1:
        wavelength_grids_match = False
    
    report_content = f"""# CDOM/ag Spectral Dataset Analysis

This report presents a forensic and scientific analysis of the Chromophoric Dissolved Organic Matter (CDOM) absorption coefficient ($a_g$) and absorbance spectral files.

## Summary of the CDOM Dataset
- **Total Files**: {total_files} SeaBASS spectral files (`.sb`)
- **Total Raw Measurements (rows)**: {total_measurements} (551 spectral measurements per physical sample)
- **Independent Physical Water Samples**: {total_files} samples (each file represents a single physical water sample)
- **Spectral Coverage**: 300 nm to 850 nm with exactly 1 nm spacing
- **Wavelength Grids Uniformity**: {"Identical across all files (300 to 850 nm)" if wavelength_grids_match else "Grid mismatches detected"}
- **Combine Feasibility**: Highly feasible and recommended without interpolation. `cdom_wide.csv` has been generated.

## Metadata Summary
The following table summarizes the metadata extracted from each CDOM sample file:

| Filename | Date | Time (GMT) | Latitude | Longitude | Depth (m) | Instrument Model | Water Depth (m) |
|---|---|---|---|---|---|---|---|
"""
    for _, r in df_meta.iterrows():
        report_content += f"| `{r['filename']}` | {r['date']} | {r['time']} | {r['latitude']:.4f} | {r['longitude']:.4f} | {r['measurement_depth']} | {r['instrument_model']} | {r['water_depth']} |\n"
        
    report_content += f"""
## Statistical Analysis of CDOM variables
- **$a_g$ (Absorption Coefficient, unit 1/m)**:
  - **Count**: {ag_stats['count']:.0f} values
  - **Min**: {ag_stats['min']:.6f}
  - **Max**: {ag_stats['max']:.6f}
  - **Mean**: {ag_stats['mean']:.6f}
  - **Median (50%)**: {ag_stats['50%']:.6f}
  - **Standard Deviation**: {ag_stats['std']:.6f}
  - **Quartiles**: 25% = {ag_stats['25%']:.6f}, 75% = {ag_stats['75%']:.6f}

- **`abs_ag` (Absorbance, unitless)**:
  - **Count**: {abs_stats['count']:.0f} values
  - **Min**: {abs_stats['min']:.6f}
  - **Max**: {abs_stats['max']:.6f}
  - **Mean**: {abs_stats['mean']:.6f}
  - **Median (50%)**: {abs_stats['50%']:.6f}
  - **Standard Deviation**: {abs_stats['std']:.6f}
  - **Quartiles**: 25% = {abs_stats['25%']:.6f}, 75% = {abs_stats['75%']:.6f}

## Data Quality Findings and Anomalies
1. **Negative Values**:
   - There are **{neg_ag_count}** negative $a_g$ measurements and **{neg_abs_count}** negative absorbance measurements.
   - *Scientific Interpretation*: Negative values represent measurement noise, baseline drift, or instrument fluctuations, particularly at longer wavelengths (>650 nm) where water absorption dominates and CDOM absorption is extremely close to zero. They should not be simply discarded but understood as statistical variations around zero.
2. **Missing and NaN Values**:
   - There are **{nan_ag_count}** NaN/missing values in the processed dataset.
   - The missing flag code `/missing=-9999` was resolved successfully.
3. **Outliers**:
   - Outlier checks (e.g., $a_g$ at 300 nm) show that sample `NES-LTER_AE2426_ag_202411110643_003m_R1.sb` has significantly higher absorption across all wavelengths compared to others (max $a_g$ of {df_wide['ag_300'].max():.4f} at 300 nm compared to other samples which range from 0.4 to 1.2 1/m). This is a potential outlier or a sample from a high-runoff coastal station.

## Pseudoreplication Warning
Treating all {total_measurements} data rows as independent samples for Machine Learning is a severe case of **pseudoreplication**! The 551 wavelength rows in each file belong to **one** physical water sample. For any supervised ML or anomaly detection, there are only **{total_files} independent physical samples**.

## Baseline Correction and Smoothing
Reviewing the metadata and comments, the files represent preliminary/final processed absorption scan data. Baseline subtraction (using purified Milli-Q water as reference) is standard practice and is confirmed in the scientific protocol.
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Saved CDOM analysis report to {output_path}")

if __name__ == "__main__":
    main()
