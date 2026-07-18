import unittest
import numpy as np
import pandas as pd
from src.features.feature_engineering import TemporalFeatureExtractor
from src.data.preprocessing import GroupMedianImputer, DepthImputer, build_caml_preprocessing_pipeline, build_habsos_preprocessing_pipeline

class TestPhase2(unittest.TestCase):
    def test_temporal_feature_extractor_cyclic(self):
        """Assert TemporalFeatureExtractor creates correct columns and correct cyclic boundaries."""
        df_mock = pd.DataFrame({
            'date_str': ['2018-01-15', '2018-07-15'],
            'date_int': [20180115, 20180715]
        })
        
        # Test string format parsing
        extractor_str = TemporalFeatureExtractor(date_col='date_str')
        df_str_res = extractor_str.fit_transform(df_mock)
        
        self.assertIn('Month', df_str_res.columns)
        self.assertIn('Season', df_str_res.columns)
        self.assertIn('Month_sin', df_str_res.columns)
        self.assertIn('Month_cos', df_str_res.columns)
        
        # Check January Month value is 1
        self.assertEqual(df_str_res.loc[0, 'Month'], 1.0)
        # Check Season classifications
        self.assertEqual(df_str_res.loc[0, 'Season'], 'Winter')
        self.assertEqual(df_str_res.loc[1, 'Season'], 'Summer')

        # Test integer format parsing
        extractor_int = TemporalFeatureExtractor(date_col='date_int', date_format='yyyymmdd')
        df_int_res = extractor_int.fit_transform(df_mock)
        self.assertEqual(df_int_res.loc[0, 'Month'], 1.0)

    def test_group_median_imputer(self):
        """Assert GroupMedianImputer correctly imputes values using groups and adds missingness flags."""
        df_train = pd.DataFrame({
            'STATE_ID': ['FL', 'FL', 'FL', 'TX', 'TX'],
            'Month': [1.0, 1.0, 2.0, 1.0, 2.0],
            'SALINITY': [30.0, 32.0, 28.0, 20.0, 22.0]
        })
        
        df_test = pd.DataFrame({
            'STATE_ID': ['FL', 'TX', 'FL', 'MS'], # MS is unseen state
            'Month': [1.0, 1.0, 3.0, 1.0],      # FL in Month 3 is unseen group
            'SALINITY': [np.nan, np.nan, np.nan, np.nan]
        })

        imputer = GroupMedianImputer(
            target_cols=['SALINITY'], 
            group_cols=['STATE_ID', 'Month'], 
            fallback_col='STATE_ID'
        )
        
        imputer.fit(df_train)
        df_imputed = imputer.transform(df_test)
        
        # 1. FL in Month 1 should impute with median of [30, 32] = 31.0
        self.assertEqual(df_imputed.loc[0, 'SALINITY'], 31.0)
        # 2. TX in Month 1 should impute with 20.0
        self.assertEqual(df_imputed.loc[1, 'SALINITY'], 20.0)
        # 3. FL in Month 3 (unseen group) fallback to STATE FL median (all FL values: [30, 32, 28] median = 30.0)
        self.assertEqual(df_imputed.loc[2, 'SALINITY'], 30.0)
        # 4. MS in Month 1 (unseen state/group) fallback to global median (all train values: [30, 32, 28, 20, 22] median = 28.0)
        self.assertEqual(df_imputed.loc[3, 'SALINITY'], 28.0)
        
        # Check missingness indicator column
        self.assertTrue(df_imputed['SALINITY_is_missing'].all())

    def test_pipeline_no_nan_outputs(self):
        """Assert pipelines output finite numeric values with no NaNs."""
        df_mock = pd.DataFrame({
            'STATE_ID': ['FL', 'TX', 'FL'],
            'SAMPLE_DATE': ['2018-05-12', '2019-11-20', '2020-01-01'],
            'LATITUDE': [26.5, 29.0, 27.2],
            'LONGITUDE': [-82.1, -95.3, -80.9],
            'SAMPLE_DEPTH': [0.5, np.nan, 2.0],  # test depth imputer
            'SALINITY': [32.0, np.nan, 29.5],    # test group imputer
            'WATER_TEMP': [24.0, 18.5, np.nan]   # test group imputer
        })

        # Apply Temporal Extraction first
        extractor = TemporalFeatureExtractor(date_col='SAMPLE_DATE')
        df_extracted = extractor.fit_transform(df_mock)
        
        # Build HABSOS preprocessing pipeline
        pipeline = build_habsos_preprocessing_pipeline()
        
        # Fit on train data
        pipeline.fit(df_extracted)
        processed_arr = pipeline.transform(df_extracted)
        
        # Check shape is 2D and contains numeric elements with no NaNs
        self.assertEqual(len(processed_arr.shape), 2)
        self.assertFalse(np.isnan(processed_arr).any())

if __name__ == "__main__":
    unittest.main()
