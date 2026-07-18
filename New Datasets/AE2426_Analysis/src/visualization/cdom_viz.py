import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys

# Add directory to sys path
analysis_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(analysis_root)

def main():
    project_root = r"P:\5th semester\Embedded Systems\Capstone Project"
    analysis_root = os.path.join(project_root, "New Datasets", "AE2426_Analysis")
    
    # Load processed data
    df_long = pd.read_csv(os.path.join(analysis_root, "data", "processed", "cdom_long.csv"))
    df_meta = pd.read_csv(os.path.join(analysis_root, "metadata", "cdom_sample_metadata.csv"))
    
    fig_dir = os.path.join(analysis_root, "figures", "cdom")
    os.makedirs(fig_dir, exist_ok=True)
    
    sns.set_theme(style="whitegrid")
    
    # 1. Overlay of all ag spectra
    plt.figure(figsize=(10, 6))
    for filename in df_long["filename"].unique():
        sub = df_long[df_long["filename"] == filename]
        # Highlight the outlier file
        if "202411110643" in filename:
            plt.plot(sub["wavelength"], sub["ag"], label=f"{filename} (Outlier)", color="red", linewidth=2.5, alpha=0.9)
        else:
            plt.plot(sub["wavelength"], sub["ag"], color="steelblue", alpha=0.5, linewidth=1.0)
    plt.xlabel("Wavelength (nm)", fontsize=12)
    plt.ylabel("Absorption Coefficient $a_g$ (1/m)", fontsize=12)
    plt.title("CDOM Absorption Spectra ($a_g$) Overlaid - Cruise AE2426", fontsize=14)
    plt.legend()
    plt.savefig(os.path.join(fig_dir, "cdom_ag_overlaid.png"), dpi=150, bbox_inches="tight")
    plt.close()
    
    # 2. Overlay of all abs_ag spectra
    plt.figure(figsize=(10, 6))
    for filename in df_long["filename"].unique():
        sub = df_long[df_long["filename"] == filename]
        if "202411110643" in filename:
            plt.plot(sub["wavelength"], sub["abs_ag"], label=f"{filename} (Outlier)", color="red", linewidth=2.5, alpha=0.9)
        else:
            plt.plot(sub["wavelength"], sub["abs_ag"], color="seagreen", alpha=0.5, linewidth=1.0)
    plt.xlabel("Wavelength (nm)", fontsize=12)
    plt.ylabel("Absorbance (unitless)", fontsize=12)
    plt.title("CDOM Absorbance Spectra (`abs_ag`) Overlaid - Cruise AE2426", fontsize=14)
    plt.legend()
    plt.savefig(os.path.join(fig_dir, "cdom_abs_overlaid.png"), dpi=150, bbox_inches="tight")
    plt.close()

    # 3. Spectral mean and standard deviation
    # Pivot df_long to calculate mean and std per wavelength
    df_pivot = df_long.pivot(index="wavelength", columns="filename", values="ag")
    mean_ag = df_pivot.mean(axis=1)
    std_ag = df_pivot.std(axis=1)
    
    plt.figure(figsize=(10, 6))
    plt.plot(mean_ag.index, mean_ag.values, color="navy", label="Mean $a_g$", linewidth=2.0)
    plt.fill_between(mean_ag.index, mean_ag.values - std_ag.values, mean_ag.values + std_ag.values, color="blue", alpha=0.2, label="±1 StdDev")
    plt.xlabel("Wavelength (nm)", fontsize=12)
    plt.ylabel("Absorption Coefficient $a_g$ (1/m)", fontsize=12)
    plt.title("CDOM Mean Spectral Profile and Variability ($a_g$)", fontsize=14)
    plt.legend()
    plt.savefig(os.path.join(fig_dir, "cdom_ag_mean_variability.png"), dpi=150, bbox_inches="tight")
    plt.close()

    # 4. Depth distribution of CDOM samples
    plt.figure(figsize=(8, 5))
    sns.histplot(df_meta["measurement_depth"], bins=8, kde=True, color="purple")
    plt.xlabel("Measurement Depth (m)", fontsize=12)
    plt.ylabel("Sample Count", fontsize=12)
    plt.title("Depth Distribution of CDOM Samples - Cruise AE2426", fontsize=14)
    plt.savefig(os.path.join(fig_dir, "cdom_depth_distribution.png"), dpi=150, bbox_inches="tight")
    plt.close()

    # 5. Spatial sampling map
    plt.figure(figsize=(9, 7))
    plt.scatter(df_meta["longitude"], df_meta["latitude"], c=df_meta["measurement_depth"], cmap="plasma", s=100, edgecolor="black")
    cbar = plt.colorbar()
    cbar.set_label("Depth (m)", fontsize=11)
    plt.xlabel("Longitude (Degrees East)", fontsize=12)
    plt.ylabel("Latitude (Degrees North)", fontsize=12)
    plt.title("Spatial Distribution of CDOM Samples - Cruise AE2426", fontsize=14)
    # Add station numbers as text labels next to points
    for idx, row in df_meta.iterrows():
        plt.text(row["longitude"] + 0.01, row["latitude"] + 0.01, f"{idx+1}", fontsize=9, weight="bold")
    plt.savefig(os.path.join(fig_dir, "cdom_spatial_map.png"), dpi=150, bbox_inches="tight")
    plt.close()

    # 6. Sampling timeline
    df_meta["datetime"] = pd.to_datetime(df_meta["date"].astype(str) + " " + df_meta["time"])
    df_meta_sorted = df_meta.sort_values("datetime")
    
    plt.figure(figsize=(10, 5))
    plt.plot(df_meta_sorted["datetime"], df_meta_sorted["measurement_depth"], marker="o", color="darkred", linestyle="-")
    plt.gca().invert_yaxis()  # Invert depth so surface is at the top
    plt.xlabel("Date & Time (GMT)", fontsize=12)
    plt.ylabel("Measurement Depth (m)", fontsize=12)
    plt.title("Sampling Timeline and Depths - Cruise AE2426", fontsize=14)
    plt.xticks(rotation=45)
    plt.savefig(os.path.join(fig_dir, "cdom_sampling_timeline.png"), dpi=150, bbox_inches="tight")
    plt.close()

    print("Generated all CDOM visualizations.")
    
    # Generate Report 04
    generate_report_04(fig_dir, os.path.join(analysis_root, "reports", "04_cdom_visual_analysis.md"))

def generate_report_04(fig_dir, output_path):
    report_content = f"""# CDOM Scientific Visualization Report

This report presents and analyzes the scientific visualizations generated from the AE2426 CDOM dataset.

## Visualizations List

### 1. CDOM Absorption Coefficient ($a_g$) Overlaid
![CDOM Absorption Coefficient Spectra Overlaid](file:///{fig_dir.replace('\\', '/')}/cdom_ag_overlaid.png)
- **Observations**: 
  - Standard exponential decay curves characteristic of CDOM absorption. Absorption is highest in the UV range (300 nm) and decays exponentially toward the near-infrared.
  - The sample `NES-LTER_AE2426_ag_202411110643_003m_R1.sb` (shown in red) stands out as an outlier with a starting $a_g$ of ~1.35 1/m at 300 nm, which is nearly double the typical value of other samples.
  - At wavelengths >650 nm, the absorption coefficient converges to values close to zero. Some files exhibit noise resulting in slight negative values at longer wavelengths.

### 2. CDOM Absorbance (`abs_ag`) Overlaid
![CDOM Absorbance Spectra Overlaid](file:///{fig_dir.replace('\\', '/')}/cdom_abs_overlaid.png)
- **Observations**:
  - Shows raw spectrophotometer absorbance readings, which match the exponential decay shape of the absorption coefficient.
  - Outlier sample again stands out significantly, reaching an absorbance value of ~0.06 at 300 nm.

### 3. CDOM Mean Spectral Profile and Variability
![CDOM Mean Spectral Profile and Variability](file:///{fig_dir.replace('\\', '/')}/cdom_ag_mean_variability.png)
- **Observations**:
  - The shaded band represents $\pm 1$ Standard Deviation.
  - The standard deviation is highest at shorter wavelengths (300 nm to 400 nm), reflecting spatial and temporal variability in water sample compositions. It decreases as the wavelength increases.

### 4. Depth Distribution of CDOM Samples
![Depth Distribution of CDOM Samples](file:///{fig_dir.replace('\\', '/')}/cdom_depth_distribution.png)
- **Observations**:
  - The sampling is concentrated in shallow surface waters, with depths between 2.5m and 4.3m. There are no deep-water samples in this CDOM set.

### 5. Spatial Sampling Map
![Spatial Sampling Map](file:///{fig_dir.replace('\\', '/')}/cdom_spatial_map.png)
- **Observations**:
  - Samples are distributed geographically across the inner shelf of the North East Shelf (NES).
  - Most CDOM sampling stations are clustered around a longitudinal transect of -70.88° East, stretching from 39.7° to 41.3° North, representing a cross-shelf transect.

### 6. Sampling Timeline
![Sampling Timeline](file:///{fig_dir.replace('\\', '/')}/cdom_sampling_timeline.png)
- **Observations**:
  - Samples were collected sequentially over a 5-day period from November 6 to November 11, 2024.
  - Sampling occurred at different hours of the day (some early morning, some mid-day, some night).
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Saved CDOM visual analysis report to {output_path}")

if __name__ == "__main__":
    main()
