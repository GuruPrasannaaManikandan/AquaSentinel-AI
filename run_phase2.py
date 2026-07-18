import os
import json
import joblib
import pandas as pd
import numpy as np
import logging
from src.utils.config import Config
from src.utils.logger import setup_logger
from src.data.loaders import CAMLLoader, HABSOSLoader
from src.features.feature_engineering import TemporalFeatureExtractor
from src.data.preprocessing import build_caml_preprocessing_pipeline, build_habsos_preprocessing_pipeline

# Setup logger
logger = setup_logger("run_phase2", "logs/phase2.log")

def run_caml_pipeline(config, processed_dir, models_dir):
    logger.info("Starting CAML Preprocessing and splitting...")
    loader = CAMLLoader(config)
    df = loader.load()
    
    # Chronological Split
    # Train: < 20200101
    # Val: 20200101 to 20201231
    # Test: >= 20210101
    train_mask = df['date'] < 20200101
    val_mask = (df['date'] >= 20200101) & (df['date'] < 20210101)
    test_mask = df['date'] >= 20210101
    
    caml_train = df[train_mask].copy()
    caml_val = df[val_mask].copy()
    caml_test = df[test_mask].copy()
    
    logger.info(f"CAML split sizes - Train: {len(caml_train)}, Val: {len(caml_val)}, Test: {len(caml_test)}")
    
    # Temporal feature extraction
    extractor = TemporalFeatureExtractor(date_col='date', date_format='yyyymmdd')
    caml_train = extractor.fit_transform(caml_train)
    caml_val = extractor.transform(caml_val)
    caml_test = extractor.transform(caml_test)
    
    # Save the splits to data/processed before applying ColumnTransformer
    # This allows sklearn pipelines to transform data dynamically during modeling
    os.makedirs(processed_dir, exist_ok=True)
    caml_train.to_csv(os.path.join(processed_dir, "caml_train.csv"), index=False)
    caml_val.to_csv(os.path.join(processed_dir, "caml_val.csv"), index=False)
    caml_test.to_csv(os.path.join(processed_dir, "caml_test.csv"), index=False)
    
    # Build and fit preprocessing pipeline strictly on training data
    preprocessor = build_caml_preprocessing_pipeline()
    preprocessor.fit(caml_train)
    
    # Save the fitted preprocessor
    os.makedirs(models_dir, exist_ok=True)
    preprocessor_path = os.path.join(models_dir, "caml_preprocessor.joblib")
    joblib.dump(preprocessor, preprocessor_path)
    logger.info(f"Fitted CAML preprocessor saved to {preprocessor_path}")
    
    return {
        'train_shape': caml_train.shape,
        'val_shape': caml_val.shape,
        'test_shape': caml_test.shape,
        'target_col': 'severity',
        'leakage_cols_dropped': ['abun', 'uid', 'date', 'time']
    }

def run_habsos_pipeline(config, processed_dir, models_dir):
    logger.info("Starting HABSOS Preprocessing and splitting...")
    loader = HABSOSLoader(config)
    df = loader.load()
    
    # Parse DATE
    df['SAMPLE_DATE_DT'] = pd.to_datetime(df['SAMPLE_DATE'], errors='coerce')
    # Default fallback for unparseable dates
    if df['SAMPLE_DATE_DT'].isnull().any():
        df['SAMPLE_DATE_DT'] = df['SAMPLE_DATE_DT'].fillna(pd.Timestamp('2018-06-15'))
        
    # Map raw HABSOS categories to 3 ecological threat levels
    target_mapping = {
        'not observed': 'normal',
        'very low': 'normal',
        'low': 'warning',
        'medium': 'warning',
        'high': 'critical'
    }
    df['CATEGORY'] = df['CATEGORY'].map(target_mapping)
        
    # Chronological Split
    # Train: < 2021-01-01
    # Val: 2021-01-01 to 2022-12-31
    # Test: >= 2023-01-01
    train_mask = df['SAMPLE_DATE_DT'] < pd.Timestamp('2021-01-01')
    val_mask = (df['SAMPLE_DATE_DT'] >= pd.Timestamp('2021-01-01')) & (df['SAMPLE_DATE_DT'] < pd.Timestamp('2023-01-01'))
    test_mask = df['SAMPLE_DATE_DT'] >= pd.Timestamp('2023-01-01')
    
    habsos_train = df[train_mask].copy()
    habsos_val = df[val_mask].copy()
    habsos_test = df[test_mask].copy()
    
    logger.info(f"HABSOS split sizes - Train: {len(habsos_train)}, Val: {len(habsos_val)}, Test: {len(habsos_test)}")
    
    # Temporal feature extraction
    extractor = TemporalFeatureExtractor(date_col='SAMPLE_DATE')
    habsos_train = extractor.fit_transform(habsos_train)
    habsos_val = extractor.transform(habsos_val)
    habsos_test = extractor.transform(habsos_test)
    
    # Save the splits to data/processed before applying ColumnTransformer
    habsos_train.to_csv(os.path.join(processed_dir, "habsos_train.csv"), index=False)
    habsos_val.to_csv(os.path.join(processed_dir, "habsos_val.csv"), index=False)
    habsos_test.to_csv(os.path.join(processed_dir, "habsos_test.csv"), index=False)
    
    # Build and fit preprocessing pipeline strictly on training data
    pipeline = build_habsos_preprocessing_pipeline()
    pipeline.fit(habsos_train)
    
    # Save the fitted pipeline
    pipeline_path = os.path.join(models_dir, "habsos_preprocessor.joblib")
    joblib.dump(pipeline, pipeline_path)
    logger.info(f"Fitted HABSOS preprocessor saved to {pipeline_path}")
    
    # Calculate HABSOS category mapping distribution on train set
    category_dist = habsos_train['CATEGORY'].value_counts(dropna=False).to_dict()
    
    return {
        'train_shape': habsos_train.shape,
        'val_shape': habsos_val.shape,
        'test_shape': habsos_test.shape,
        'target_col': 'CATEGORY',
        'category_distribution_train': category_dist,
        'leakage_cols_dropped': [
            'CELLCOUNT', 'GENUS', 'SPECIES', 'CELLCOUNT_UNIT', 'CELLCOUNT_QA',
            'SALINITY_QA', 'WATER_TEMP_QA', 'WIND_DIR', 'WIND_SPEED', 'WIND_DIR_QA',
            'WIND_SPEED_QA', 'OBJECTID', 'DESCRIPTION', 'Unnamed: 2', 'Unnamed: 27'
        ]
    }

def main():
    logger.info("Initializing Phase 2 Preprocessing Pipeline...")
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(workspace_dir, "config", "config.yaml")
    config = Config(config_path)
    
    processed_dir = config.get_path("processed_dir", "data/processed")
    models_dir = config.get_path("models_dir", "models")
    
    # Run pipelines
    caml_meta = run_caml_pipeline(config, processed_dir, models_dir)
    habsos_meta = run_habsos_pipeline(config, processed_dir, models_dir)
    
    # Save split metadata to processed folder
    meta_path = os.path.join(processed_dir, "split_metadata.json")
    metadata = {
        'project': config.get("project", {}).get("name", "aquatic-ais-iot"),
        'caml': caml_meta,
        'habsos': habsos_meta
    }
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)
        
    logger.info(f"Metadata file successfully saved to {meta_path}")
    logger.info("Phase 2 Pipeline successfully completed!")

if __name__ == "__main__":
    main()
