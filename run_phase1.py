import os
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from src.utils.config import Config
from src.utils.logger import setup_logger
from src.data.loaders import CAMLLoader, HABSOSLoader
from src.data.validation import DatasetValidator

# Setup logger
logger = setup_logger("run_phase1", "logs/phase1.log")

def copy_raw_files_if_needed(config):
    """
    Ensure the raw files are copied from the workspace root (where the user uploaded them)
    into the data/raw subdirectories defined by config.yaml.
    """
    raw_dir = config.get_path("raw_dir")
    caml_file = config.get_dataset_config("caml").get("raw_file")
    caml_docs = config.get_dataset_config("caml").get("documents_archive")
    habsos_archive = config.get_dataset_config("habsos").get("raw_archive")

    caml_raw_dest = os.path.join(raw_dir, "caml")
    habsos_raw_dest = os.path.join(raw_dir, "habsos")
    
    os.makedirs(caml_raw_dest, exist_ok=True)
    os.makedirs(habsos_raw_dest, exist_ok=True)

    for filename, dest_dir in [
        (caml_file, caml_raw_dest),
        (caml_docs, caml_raw_dest),
        (habsos_archive, habsos_raw_dest)
    ]:
        dest_path = os.path.join(dest_dir, filename)
        if not os.path.exists(dest_path):
            if os.path.exists(filename):
                logger.info(f"Copying raw file {filename} to {dest_dir}")
                shutil.copy2(filename, dest_path)
            else:
                logger.warning(f"Raw source file {filename} not found in workspace root or {dest_path}")

def generate_caml_plots(df, figures_dir):
    """Generates analytical plots for the CAML dataset."""
    logger.info("Generating plots for CAML...")
    os.makedirs(figures_dir, exist_ok=True)
    
    # Set styling
    sns.set_theme(style="whitegrid")
    
    # 1. Severity Distribution
    plt.figure(figsize=(8, 5))
    sns.countplot(x='severity', data=df, palette="viridis")
    plt.title('Cyanobacteria Abundance Severity Class Distribution (CAML)', fontsize=14)
    plt.xlabel('Severity Level (1=Low/None, 5=Extreme)', fontsize=12)
    plt.ylabel('Observation Count', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, 'caml_severity_distribution.png'), dpi=150)
    plt.close()
    
    # 2. Abundance log distribution
    plt.figure(figsize=(8, 5))
    # Filter 0 for log log transformation
    df_non_zero = df[df['abun'] > 0]
    sns.histplot(np.log10(df_non_zero['abun']), kde=True, bins=30, color='teal')
    plt.title('Distribution of Log10(Cyanobacteria Abundance + 1) (CAML)', fontsize=14)
    plt.xlabel('Log10(cells/L)', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, 'caml_abundance_log_distribution.png'), dpi=150)
    plt.close()
    
    # 3. Correlation Heatmap
    plt.figure(figsize=(8, 6))
    corr_cols = ['lat', 'lon', 'abun', 'severity', 'distance_to_water_m']
    corr = df[corr_cols].corr()
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5)
    plt.title('Feature Correlation Matrix (CAML)', fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, 'caml_correlation_heatmap.png'), dpi=150)
    plt.close()
    
    # 4. Temporal Trend
    plt.figure(figsize=(10, 5))
    df_date = df.copy()
    df_date['parsed_date'] = pd.to_datetime(df_date['date'], format='%Y%m%d', errors='coerce')
    df_date['YearMonth'] = df_date['parsed_date'].dt.to_period('M')
    df_grouped = df_date.groupby('YearMonth').size()
    df_grouped.index = df_grouped.index.to_timestamp()
    plt.plot(df_grouped.index, df_grouped.values, marker='o', color='blue', linestyle='-', linewidth=1.5)
    plt.title('Observations Density Over Time (CAML)', fontsize=14)
    plt.xlabel('Timeline', fontsize=12)
    plt.ylabel('Monthly Samples Count', fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, 'caml_temporal_distribution.png'), dpi=150)
    plt.close()

def generate_habsos_plots(df, figures_dir):
    """Generates analytical plots for the HABSOS dataset."""
    logger.info("Generating plots for HABSOS...")
    os.makedirs(figures_dir, exist_ok=True)
    sns.set_theme(style="whitegrid")
    
    # 1. Category Distribution
    plt.figure(figsize=(8, 5))
    category_order = ['not observed', 'very low', 'low', 'medium', 'high']
    sns.countplot(x='CATEGORY', data=df, order=category_order, palette="magma")
    plt.title('HAB Category Class Distribution (HABSOS)', fontsize=14)
    plt.xlabel('Bloom Risk Category', fontsize=12)
    plt.ylabel('Observation Count', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, 'habsos_category_distribution.png'), dpi=150)
    plt.close()
    
    # 2. Cell Count log distribution (non-zero)
    plt.figure(figsize=(8, 5))
    df_non_zero = df[df['CELLCOUNT'] > 0]
    sns.histplot(np.log10(df_non_zero['CELLCOUNT']), kde=True, bins=30, color='crimson')
    plt.title('Distribution of Log10(Karenia brevis Cell Count) (HABSOS)', fontsize=14)
    plt.xlabel('Log10(cells/L)', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, 'habsos_cellcount_log_distribution.png'), dpi=150)
    plt.close()
    
    # 3. Spatial distribution map
    plt.figure(figsize=(10, 8))
    # Select a subset of data to avoid overcrowding the plot
    df_sample = df.sample(n=min(len(df), 20000), random_state=42)
    sc = plt.scatter(df_sample['LONGITUDE'], df_sample['LATITUDE'], 
                     c=np.log10(df_sample['CELLCOUNT'] + 1), 
                     cmap='YlOrRd', s=8, alpha=0.6)
    plt.colorbar(sc, label='Log10(Cell Count + 1) cells/L')
    plt.title('Geographical Distribution & Cell Counts of Karenia brevis (HABSOS Sample)', fontsize=14)
    plt.xlabel('Longitude', fontsize=12)
    plt.ylabel('Latitude', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, 'habsos_geographic_distribution.png'), dpi=150)
    plt.close()
    
    # 4. Correlation of environmental parameters
    plt.figure(figsize=(8, 6))
    env_cols = ['LATITUDE', 'LONGITUDE', 'CELLCOUNT', 'SALINITY', 'WATER_TEMP', 'SAMPLE_DEPTH']
    corr = df[env_cols].corr()
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5)
    plt.title('Environmental Feature Correlation Matrix (HABSOS)', fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, 'habsos_correlation_heatmap.png'), dpi=150)
    plt.close()

def write_caml_report(val_results, df, report_path):
    """Writes the CAML data audit report in markdown format."""
    logger.info(f"Writing CAML audit report to {report_path}")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    severity_dist = df['severity'].value_counts(dropna=False)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"""# CAML Dataset Quality Audit Report

## 1. Dataset Shape & Structures
- **Name:** {val_results['dataset_name']}
- **Total Rows:** {val_results['row_count']}
- **Total Columns:** {val_results['column_count']}
- **Detected Duplicate Rows:** {val_results['duplicate_count']}

## 2. Columns & Data Types
| Column | DataType | Null Count | Null % | Range / Unique Values |
| --- | --- | --- | --- | --- |
""")
        for col in df.columns:
            null_cnt = val_results['nulls'][col]['null_count']
            null_pct = val_results['nulls'][col]['null_pct']
            dtype = str(df[col].dtype)
            
            if df[col].dtype in [np.float64, np.int64]:
                rng = f"[{df[col].min()}, {df[col].max()}]"
            else:
                rng = f"{df[col].nunique()} unique values"
                
            f.write(f"| {col} | {dtype} | {null_cnt} | {null_pct:.4f}% | {rng} |\n")
            
        f.write(f"""
## 3. Geographic Bounding Box
- **Latitude Bounds:** [{val_results['coordinates']['lat_min']}, {val_results['coordinates']['lat_max']}]
- **Longitude Bounds:** [{val_results['coordinates']['lon_min']}, {val_results['coordinates']['lon_max']}]
- **Invalid Coordinate Formats:** {val_results['coordinates']['invalid_latitudes'] + val_results['coordinates']['invalid_longitudes']}

## 4. Class Distribution (Target Candidate: severity)
| Severity Level | Count | Percentage |
| --- | --- | --- |
""")
        for level, count in severity_dist.items():
            pct = (count / len(df)) * 100
            f.write(f"| Level {level} | {count} | {pct:.2f}% |\n")

        f.write(f"""
## 5. Potential Outlier Detections
- **Abundance (cells/L) Statistics:**
  - Mean: {df['abun'].mean():.2f}
  - Std Dev: {df['abun'].std():.2f}
  - Max: {df['abun'].max()} (Potential outlier check: 75th percentile is {df['abun'].quantile(0.75):.2f})
  
## 6. Columns recommended to DROP in ML Modeling
- `uid`: Unique index identifier, carries no predictive information.
- `data_provider`: High cardinality categoric indicator of agency, might lead to data leakage if agencies monitor specific states.
- `date` / `time`: Dates should not be fed directly to avoid temporal sequence leakage; extract features like Month/Season instead.
""")

def write_habsos_report(val_results, df, report_path):
    """Writes the HABSOS data audit report in markdown format."""
    logger.info(f"Writing HABSOS audit report to {report_path}")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    category_dist = df['CATEGORY'].value_counts(dropna=False)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"""# HABSOS Dataset Quality Audit Report

## 1. Dataset Shape & Structures
- **Name:** {val_results['dataset_name']}
- **Total Rows:** {val_results['row_count']}
- **Total Columns:** {val_results['column_count']}
- **Detected Duplicate Rows:** {val_results['duplicate_count']}

## 2. Columns & Data Types
| Column | DataType | Null Count | Null % | Range / Unique Values |
| --- | --- | --- | --- | --- |
""")
        for col in df.columns:
            null_cnt = val_results['nulls'][col]['null_count']
            null_pct = val_results['nulls'][col]['null_pct']
            dtype = str(df[col].dtype)
            
            if df[col].dtype in [np.float64, np.int64]:
                rng = f"[{df[col].min()}, {df[col].max()}]"
            else:
                rng = f"{df[col].nunique()} unique values"
                
            f.write(f"| {col} | {dtype} | {null_cnt} | {null_pct:.4f}% | {rng} |\n")
            
        f.write(f"""
## 3. Geographic Bounding Box
- **Latitude Bounds:** [{val_results['coordinates']['lat_min']}, {val_results['coordinates']['lat_max']}]
- **Longitude Bounds:** [{val_results['coordinates']['lon_min']}, {val_results['coordinates']['lon_max']}]
- **Invalid Coordinate Formats:** {val_results['coordinates']['invalid_latitudes'] + val_results['coordinates']['invalid_longitudes']}

## 4. Class Distribution (Target Candidate: CATEGORY / CELLCOUNT)
| Bloom Risk Category | Count | Percentage |
| --- | --- | --- |
""")
        for category, count in category_dist.items():
            pct = (count / len(df)) * 100
            f.write(f"| {category} | {count} | {pct:.2f}% |\n")

        f.write(f"""
## 5. Potential Outlier Detections
- **CELLCOUNT (cells/L) Statistics:**
  - Mean: {df['CELLCOUNT'].mean():.2f}
  - Std Dev: {df['CELLCOUNT'].std():.2f}
  - Max: {df['CELLCOUNT'].max()}
- **Water Salinity (PPT) Statistics:**
  - Mean: {df['SALINITY'].mean():.2f} (Null: {val_results['nulls']['SALINITY']['null_pct']:.2f}%)
- **Water Temperature (C) Statistics:**
  - Mean: {df['WATER_TEMP'].mean():.2f} (Null: {val_results['nulls']['WATER_TEMP']['null_pct']:.2f}%)

## 6. Columns recommended to DROP in ML Modeling
- `GENUS` and `SPECIES`: 100% constant value (`Karenia brevis`).
- `CELLCOUNT_UNIT`: 100% constant value (`cells/L`).
- `CELLCOUNT_QA`, `SALINITY_QA`, `WATER_TEMP_QA`, `WIND_DIR_QA`, `WIND_SPEED_QA`: Data quality flags that represent post-collection attributes.
- `OBJECTID`: Database integer index.
- `Unnamed: 2` and `Unnamed: 27`: Empty columns.
- `WIND_DIR` and `WIND_SPEED`: >99% missing data.
""")

def write_compatibility_report(caml_df, habsos_df, report_path):
    """Writes the dataset compatibility and multi-model assessment report."""
    logger.info(f"Writing compatibility report to {report_path}")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"""# Dataset Compatibility Assessment

This document assesses whether the CAML Cyanobacteria Abundance dataset and the HABSOS Harmful Algal Bloom dataset can be merged, or if they should remain independent components in a multi-model architecture.

## Comparison Summary

| Metric / Dimension | CAML Dataset | HABSOS Dataset |
| --- | --- | --- |
| **Target Organism** | Cyanobacteria (Blue-green algae, multiple genera) | *Karenia brevis* (Dinoflagellate) |
| **Water Ecosystem** | Inland / Freshwater (Lakes, rivers, reservoirs) | Marine / Coastal Saltwater |
| **Geographic Span** | Contiguous United States (Lat: {caml_df['lat'].min():.2f} to {caml_df['lat'].max():.2f}) | Gulf of Mexico (Lat: {habsos_df['LATITUDE'].min():.2f} to {habsos_df['LATITUDE'].max():.2f}) |
| **Temporal Span** | 2013-01-04 to 2021-12-29 | 1953-08-19 to 2024-03-25 |
| **Primary Predictor** | Abundance / distance to water | Cell counts, water salinity, water temp |
| **Target Structure** | Integer severity level (1-5) | Categorical level (not observed to high) / numeric cell count |

## Assessment Results

1. **Direct Merging Feasibility:**
   - **Scientifically Incorrect:** Cyanobacteria thrives in freshwater ecosystems, whereas *Karenia brevis* is a marine organism that grows in highly saline environments. Concatenating them into a single tabular file would force models to learn conflicting physical thresholds (e.g. salinity ~35 PPT triggers red tide blooms, but kills cyanobacteria; temperature thresholds differ).
   - **Feature Incongruence:** HABSOS features detailed marine parameters (`SALINITY` and `WATER_TEMP`), while CAML features geographical buffers like `distance_to_water_m`. Merging would result in ~50% missing fields for all records.

2. **Recommended Decision Support Architecture:**
   - **Multi-Model Routing Architecture:** Keep the models separate.
   - **Model A (Freshwater Cyanobacteria Model):** Trained on CAML. Predicts cyanobacteria severity based on geographical inputs, month, and water distance.
   - **Model B (Marine Harmful Algal Bloom Model):** Trained on HABSOS. Predicts red tide probability and category based on latitude, longitude, salinity, temperature, and depth.
   - **IoT Gateway Routing Logic:** The virtual IoT sensor nodes feed temperature, pH, salinity, and turbidity. When the backend receives sensor readings, it evaluates the **Salinity** level:
     - **Salinity < 5 PPT (Freshwater):** Invokes Model A.
     - **Salinity >= 5 PPT (Saltwater/Marine):** Invokes Model B.
     - **This routing mechanism achieves a modular, scientifically clean, and physically sound prediction system.**
""")

def main():
    logger.info("Initializing Phase 1 Pipeline...")
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(workspace_dir, "config", "config.yaml")
    config = Config(config_path)
    
    # 1. Copy raw files into proper locations if they are in root
    copy_raw_files_if_needed(config)
    
    # 2. Create Loader objects
    caml_loader = CAMLLoader(config)
    habsos_loader = HABSOSLoader(config)
    
    # 3. Run extractions
    caml_loader.extract()
    habsos_loader.extract()
    
    # 4. Load datasets into DataFrames
    caml_df = caml_loader.load()
    habsos_df = habsos_loader.load()
    
    # 5. Initialize Validator
    caml_validator = DatasetValidator("CAML")
    habsos_validator = DatasetValidator("HABSOS")
    
    # Validate CAML
    caml_numeric = ['abun', 'severity', 'distance_to_water_m']
    caml_val_results = caml_validator.validate_all(caml_df, 'lat', 'lon', caml_numeric)
    
    # Validate HABSOS
    habsos_numeric = ['CELLCOUNT', 'SALINITY', 'WATER_TEMP', 'SAMPLE_DEPTH']
    habsos_val_results = habsos_validator.validate_all(habsos_df, 'LATITUDE', 'LONGITUDE', habsos_numeric)
    
    # 6. Generate Reports
    audit_dir = config.get_path("audit_dir")
    os.makedirs(audit_dir, exist_ok=True)
    
    write_caml_report(caml_val_results, caml_df, os.path.join(audit_dir, "caml_audit_report.md"))
    write_habsos_report(habsos_val_results, habsos_df, os.path.join(audit_dir, "habsos_audit_report.md"))
    write_compatibility_report(caml_df, habsos_df, os.path.join(audit_dir, "compatibility_assessment.md"))
    
    # 7. Generate Visualizations
    figures_dir = config.get_path("figures_dir")
    generate_caml_plots(caml_df, figures_dir)
    generate_habsos_plots(habsos_df, figures_dir)
    
    logger.info("Phase 1 Pipeline successfully completed!")

if __name__ == "__main__":
    main()
