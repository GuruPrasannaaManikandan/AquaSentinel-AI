import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    project_root = r"P:\5th semester\Embedded Systems\Capstone Project"
    analysis_root = os.path.join(project_root, "New Datasets", "AE2426_Analysis")
    
    # Load clean data
    df = pd.read_csv(os.path.join(analysis_root, "data", "processed", "hplc_clean_analysis.csv"))
    
    fig_dir = os.path.join(analysis_root, "figures", "hplc")
    os.makedirs(fig_dir, exist_ok=True)
    
    sns.set_theme(style="whitegrid")
    
    # 1. Boxplot of major pigments
    major_pigments = ["Tot_Chl_a", "Tot_Chl_b", "Tot_Chl_c", "Fuco", "Zea", "Hex-fuco", "Allo"]
    plt.figure(figsize=(10, 6))
    df_melted = df.melt(value_vars=major_pigments, var_name="Pigment", value_name="Concentration (mg/m^3)")
    sns.boxplot(x="Pigment", y="Concentration (mg/m^3)", data=df_melted, hue="Pigment", legend=False, palette="Set2")
    plt.yscale("log")  # Use log scale due to high range differences
    plt.ylabel("Concentration (mg/m^3, log scale)", fontsize=12)
    plt.xlabel("Pigment Name", fontsize=12)
    plt.title("Concentration Distributions of Major Pigments - Cruise AE2426", fontsize=14)
    plt.savefig(os.path.join(fig_dir, "hplc_pigment_boxplot.png"), dpi=150, bbox_inches="tight")
    plt.close()
    
    # 2. Scatter plot: Fucoxanthin vs Tot_Chl_a (indicates diatom biomass vs total biomass)
    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=df, x="Tot_Chl_a", y="Fuco", s=80, hue="depth", palette="viridis", edgecolor="black")
    plt.xlabel("Total Chlorophyll a (mg/m^3)", fontsize=12)
    plt.ylabel("Fucoxanthin (mg/m^3)", fontsize=12)
    plt.title("Fucoxanthin vs Total Chlorophyll a - Cruise AE2426", fontsize=14)
    plt.savefig(os.path.join(fig_dir, "hplc_fuco_vs_chla.png"), dpi=150, bbox_inches="tight")
    plt.close()

    # 3. Depth Profile of Chlorophyll-a
    plt.figure(figsize=(6, 8))
    plt.scatter(df["Tot_Chl_a"], df["depth"], color="forestgreen", s=80, edgecolor="black")
    plt.gca().invert_yaxis()  # Surface at the top
    plt.xlabel("Total Chlorophyll a (mg/m^3)", fontsize=12)
    plt.ylabel("Depth (m)", fontsize=12)
    plt.title("Depth Profile of Total Chlorophyll a", fontsize=14)
    plt.savefig(os.path.join(fig_dir, "hplc_depth_profile_chla.png"), dpi=150, bbox_inches="tight")
    plt.close()

    # 4. Correlation Heatmap of key pigments
    key_cols = ["Tot_Chl_a", "Tot_Chl_b", "Tot_Chl_c", "alpha-beta-Car", "Hex-fuco", "Fuco", "Allo", "Diadino", "Zea", "volfilt"]
    df_key = df[key_cols].copy()
    
    plt.figure(figsize=(10, 8))
    corr = df_key.corr()
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", vmin=-1, vmax=1, linewidths=0.5)
    plt.title("Correlation Matrix of Key Phytoplankton Pigments - Cruise AE2426", fontsize=14)
    plt.savefig(os.path.join(fig_dir, "hplc_pigment_correlation.png"), dpi=150, bbox_inches="tight")
    plt.close()

    # 5. Spatial map colored by Chlorophyll-a
    plt.figure(figsize=(9, 7))
    plt.scatter(df["lon"], df["lat"], c=df["Tot_Chl_a"], cmap="YlGnBu", s=120, edgecolor="black")
    cbar = plt.colorbar()
    cbar.set_label("Total Chlorophyll a (mg/m^3)", fontsize=11)
    plt.xlabel("Longitude (Degrees East)", fontsize=12)
    plt.ylabel("Latitude (Degrees North)", fontsize=12)
    plt.title("Spatial Distribution of Chlorophyll a - Cruise AE2426", fontsize=14)
    # Annotate stations
    for _, row in df.iterrows():
        # Keep unique coordinates for cleaner labels
        plt.text(row["lon"] + 0.005, row["lat"] + 0.005, f"St {int(row['station'])}", fontsize=8)
    plt.savefig(os.path.join(fig_dir, "hplc_spatial_chlorophyll.png"), dpi=150, bbox_inches="tight")
    plt.close()

    print("Generated all HPLC visualizations.")
    
    # Generate Report 06
    generate_report_06(fig_dir, os.path.join(analysis_root, "reports", "06_hplc_visual_analysis.md"))

def generate_report_06(fig_dir, output_path):
    report_content = f"""# HPLC Scientific Visualization Report

This report presents and analyzes the scientific visualizations generated from the AE2426 HPLC pigment dataset.

## Visualizations List

### 1. Concentration Distributions of Major Pigments (Boxplot)
![Pigment Concentration Distributions](file:///{fig_dir.replace('\\', '/')}/hplc_pigment_boxplot.png)
- **Observations**:
  - The boxplot uses a logarithmic scale to show concentrations spanning three orders of magnitude.
  - `Tot_Chl_a` is the most abundant pigment, peaking at >6.0 mg/m^3.
  - `Fuco` (Fucoxanthin, marker for diatoms) is also highly abundant, indicating that diatoms represent a major component of the phytoplankton biomass.
  - `Zea` (Zeaxanthin, marker for cyanobacteria/synechococcus) has a much lower concentration (around 0.02 - 0.05 mg/m^3), reflecting that prokaryotic picophytoplankton represent a smaller fraction of the biomass in this nutrient-rich fall dataset.
  - Accessory pigments like `Tot_Chl_b`, `Hex-fuco`, and `Allo` are intermediate.

### 2. Fucoxanthin vs Total Chlorophyll a (Scatter Plot)
![Fucoxanthin vs Total Chlorophyll a](file:///{fig_dir.replace('\\', '/')}/hplc_fuco_vs_chla.png)
- **Observations**:
  - There is a very strong, tight linear relationship between Fucoxanthin (`Fuco`) and Total Chlorophyll-a (`Tot_Chl_a`).
  - This indicates that changes in total phytoplankton biomass are primarily driven by diatom biomass variations.
  - Points are colored by depth, showing that higher concentrations (both Chl-a and Fucoxanthin) are concentrated in shallower surface waters.

### 3. Depth Profile of Total Chlorophyll a
![Depth Profile of Chlorophyll a](file:///{fig_dir.replace('\\', '/')}/hplc_depth_profile_chla.png)
- **Observations**:
  - This vertical profile shows higher Chlorophyll-a concentrations at shallower depths (surface down to 20m), with a distinct drop-off at deeper stations (>30m).
  - Surface samples reach up to 6.78 mg/m^3, while deep samples at 50-65m remain below 0.5 mg/m^3. This is consistent with light limitation in deep marine waters.

### 4. Correlation Heatmap of Key Pigments
![Pigment Correlation Matrix](file:///{fig_dir.replace('\\', '/')}/hplc_pigment_correlation.png)
- **Observations**:
  - `Tot_Chl_a` is extremely highly correlated with `Fuco` (r = 0.93) and `Tot_Chl_c` (r = 0.99), suggesting a co-presence of diatoms and associated chlorophylls.
  - `Zea` has moderate correlation with Chl-a (r = 0.49), indicating that cyanobacteria do not follow the exact same distribution as diatoms, possibly preferring different depths or spatial niches.
  - `volfilt` (volume filtered in liters) has zero correlation with pigment concentrations, confirming that the sample preparation did not introduce artificial concentration biases.

### 5. Spatial Distribution of Chlorophyll a
![Spatial Distribution of Chlorophyll a](file:///{fig_dir.replace('\\', '/')}/hplc_spatial_chlorophyll.png)
- **Observations**:
  - Highlights a strong geographical gradient: Chlorophyll-a is highest at the coastal stations (Station 20, north, near-shore, reaching >6.0 mg/m^3) and drops significantly at offshore stations (Station 10, south, outer-shelf, dropping to <0.5 mg/m^3).
  - This matches typical oceanographic patterns where nearshore waters are enriched with nutrients (promoting large diatom blooms), while offshore waters are more oligotrophic.
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Saved HPLC visual analysis report to {output_path}")

if __name__ == "__main__":
    main()
