import os
import sys
import unittest
import numpy as np
import pandas as pd

# Add the analysis workspace src directory to path to enable imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(project_root, "New Datasets", "AE2426_Analysis"))

from src.parsing.seabass_parser import SeaBASSParser
from src.matching.matching_engine import haversine_distance

class TestSeaBASSParserAndAnalysis(unittest.TestCase):
    def setUp(self):
        self.parser = SeaBASSParser()
        self.mock_content = """/begin_header
/received=20260710
/data_file_name=mock_sample.sb
/experiment=Test_Experiment
/cruise=Test_Cruise
/missing=-9999
/below_detection_limit=-8888
/delimiter=comma
/fields=wavelength,value,flag
/units=nm,1/m,none
! This is a comment
! Another comment
/end_header
300,1.23,1
301,-8888,2
302,-9999,3
303,1.45,4
"""
        self.temp_file = os.path.join(project_root, "New Datasets", "AE2426_Analysis", "tests", "temp_mock_sample.sb")
        os.makedirs(os.path.dirname(self.temp_file), exist_ok=True)
        with open(self.temp_file, "w", encoding="utf-8") as f:
            f.write(self.mock_content)

    def tearDown(self):
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)

    def test_mock_parsing(self):
        metadata, comments, df, warnings = self.parser.parse(self.temp_file)
        
        self.assertEqual(metadata["experiment"], "Test_Experiment")
        self.assertEqual(metadata["cruise"], "Test_Cruise")
        self.assertEqual(metadata["missing"], "-9999")
        self.assertEqual(len(comments), 2)
        
        self.assertEqual(list(df.columns), ["wavelength", "value", "flag"])
        self.assertEqual(len(df), 4)
        
        # Test missing values replacement
        self.assertTrue(np.isnan(df.loc[1, "value"]))  # -8888 replaced by NaN
        self.assertTrue(np.isnan(df.loc[2, "value"]))  # -9999 replaced by NaN
        
        self.assertEqual(len(warnings), 0)

    def test_malformed_columns_warning(self):
        malformed_content = """/begin_header
/received=20260710
/missing=-9999
/delimiter=comma
/fields=col1,col2
/units=none,none
/end_header
1,2
3,4,5
6
"""
        temp_malformed = os.path.join(os.path.dirname(self.temp_file), "temp_malformed.sb")
        with open(temp_malformed, "w", encoding="utf-8") as f:
            f.write(malformed_content)

        try:
            metadata, comments, df, warnings = self.parser.parse(temp_malformed)
            self.assertEqual(len(df), 3)
            self.assertEqual(len(warnings), 2)  # Two row warnings
        finally:
            if os.path.exists(temp_malformed):
                os.remove(temp_malformed)

    def test_sample_count_integrity(self):
        # Verify that there are exactly 12 CDOM files and 1 HPLC file in the original archive
        archive_dir = os.path.join(project_root, "New Datasets", "requested_files", "WHOI", "SOSIK", "NES-LTER", "AE2426", "archive")
        if os.path.exists(archive_dir):
            files = os.listdir(archive_dir)
            cdom_files = [f for f in files if "_ag_" in f and f.endswith(".sb")]
            hplc_files = [f for f in files if "_HPLC_" in f and f.endswith(".sb")]
            
            self.assertEqual(len(cdom_files), 12, "CDOM file count must be exactly 12")
            self.assertEqual(len(hplc_files), 1, "HPLC file count must be exactly 1")

    def test_prevention_of_pseudoreplication_assumptions(self):
        # Verify that each CDOM file represents exactly 1 independent sample
        # Wavelengths are features/measurements within a single sample, not independent ML observations
        archive_dir = os.path.join(project_root, "New Datasets", "requested_files", "WHOI", "SOSIK", "NES-LTER", "AE2426", "archive")
        if os.path.exists(archive_dir):
            files = sorted([f for f in os.listdir(archive_dir) if "_ag_" in f and f.endswith(".sb")])
            for f in files:
                filepath = os.path.join(archive_dir, f)
                meta, comm, df, warn = self.parser.parse(filepath)
                # Confirm that the start date and start time uniquely identify a single station/measurement
                self.assertIsNotNone(meta.get("start_date"))
                self.assertIsNotNone(meta.get("start_time"))
                self.assertIsNotNone(meta.get("measurement_depth"))
                # Wavelength rows are highly correlated (non-independent)
                corr = df["ag"].corr(df["abs_ag"])
                self.assertGreater(corr, 0.99, "ag and abs_ag must be extremely highly correlated within a single physical sample")

    def test_haversine_distance(self):
        # Test distance calculation between two known points (e.g. Woods Hole to Boston)
        # Woods Hole: 41.5265 N, -70.6731 W
        # Boston: 42.3601 N, -71.0589 W
        # Expected distance: ~98.3 km
        dist = haversine_distance(41.5265, -70.6731, 42.3601, -71.0589)
        self.assertAlmostEqual(dist / 1000.0, 98.3, delta=2.0) # Within 2km tolerance

    def test_matching_results_validation(self):
        matches_csv = os.path.join(project_root, "New Datasets", "AE2426_Analysis", "data", "processed", "cdom_hplc_match_candidates.csv")
        if os.path.exists(matches_csv):
            df_matches = pd.read_csv(matches_csv)
            self.assertEqual(len(df_matches), 12, "Should contain matching decisions for all 12 CDOM files")
            
            # Assert 11 exact matches and 1 unmatched due to depth mismatch
            self.assertEqual((df_matches["confidence"] == "EXACT").sum(), 11)
            self.assertEqual((df_matches["confidence"] == "UNMATCHED").sum(), 1)
            
            # Find the unmatched file
            unmatched_row = df_matches[df_matches["confidence"] == "UNMATCHED"].iloc[0]
            self.assertEqual(unmatched_row["cdom_filename"], "NES-LTER_AE2426_ag_202411090118_004m_R1.sb")
            self.assertEqual(unmatched_row["reason"], "No candidate within thresholds")

    def test_processed_output_schemas(self):
        long_csv = os.path.join(project_root, "New Datasets", "AE2426_Analysis", "data", "processed", "cdom_long.csv")
        wide_csv = os.path.join(project_root, "New Datasets", "AE2426_Analysis", "data", "processed", "cdom_wide.csv")
        hplc_csv = os.path.join(project_root, "New Datasets", "AE2426_Analysis", "data", "processed", "hplc_clean_analysis.csv")
        
        if os.path.exists(long_csv):
            df_long = pd.read_csv(long_csv)
            self.assertEqual(df_long.shape[0], 12 * 551)
            self.assertEqual(list(df_long.columns), ["filename", "date", "time", "lat", "lon", "depth", "wavelength", "ag", "abs_ag"])
            
        if os.path.exists(wide_csv):
            df_wide = pd.read_csv(wide_csv)
            self.assertEqual(df_wide.shape[0], 12)
            # 7 metadata cols + 551 ag cols + 551 abs_ag cols = 1109 columns
            self.assertEqual(df_wide.shape[1], 1109)
            self.assertIn("ag_300", df_wide.columns)
            self.assertIn("abs_ag_850", df_wide.columns)
            
        if os.path.exists(hplc_csv):
            df_hplc = pd.read_csv(hplc_csv)
            self.assertEqual(df_hplc.shape[0], 32)
            self.assertEqual(df_hplc.shape[1], 51)

if __name__ == "__main__":
    unittest.main()
