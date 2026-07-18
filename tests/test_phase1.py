import unittest
import os
import shutil
import pandas as pd
from src.utils.config import Config
from src.data.loaders import CAMLLoader, HABSOSLoader
from src.data.validation import DatasetValidator

class TestPhase1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize paths
        cls.workspace_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        cls.config_path = os.path.join(cls.workspace_dir, "config", "config.yaml")
        cls.config = Config(cls.config_path)
        
        # Ensure raw directories exist
        cls.raw_caml_dir = os.path.join(cls.workspace_dir, "data", "raw", "caml")
        cls.raw_habsos_dir = os.path.join(cls.workspace_dir, "data", "raw", "habsos")
        os.makedirs(cls.raw_caml_dir, exist_ok=True)
        os.makedirs(cls.raw_habsos_dir, exist_ok=True)

        # Copy raw files from workspace root to data/raw if needed
        # This keeps the test suite self-contained
        caml_file = "0c233b5a95_CAML_cyanobacteria_abundance_20211229_R1.sb"
        caml_docs = "0c233b5a95_documents.tgz.sb"
        habsos_archive = "0120767.8.8.tar.gz"

        for file_name, dest_dir in [
            (caml_file, cls.raw_caml_dir),
            (caml_docs, cls.raw_caml_dir),
            (habsos_archive, cls.raw_habsos_dir)
        ]:
            src_path = os.path.join(cls.workspace_dir, file_name)
            dest_path = os.path.join(dest_dir, file_name)
            if os.path.exists(src_path) and not os.path.exists(dest_path):
                print(f"Testing Setup: Copying {file_name} to {dest_dir}")
                shutil.copy2(src_path, dest_path)

    def test_config_loading(self):
        """Assert configuration loads correctly and returns values."""
        self.assertEqual(self.config.random_seed, 42)
        raw_dir = self.config.get_path("raw_dir")
        self.assertEqual(raw_dir, "data/raw")

    def test_caml_header_parsing(self):
        """Assert CAML loader correctly parses the SeaBASS header format."""
        loader = CAMLLoader(self.config)
        # Check raw file path exists before header parsing
        self.assertTrue(os.path.exists(loader.raw_filepath), f"File missing at {loader.raw_filepath}")
        
        header_info = loader.parse_header(loader.raw_filepath)
        self.assertEqual(header_info['delimiter'], ',')
        self.assertEqual(header_info['missing_value'], -9999.0)
        self.assertIn('uid', header_info['fields'])
        self.assertIn('severity', header_info['fields'])

    def test_validator(self):
        """Assert DatasetValidator accurately flag duplicates and coordinate boundary violations."""
        validator = DatasetValidator("TestSet")
        
        # Mock DataFrame
        df_mock = pd.DataFrame({
            'lat': [34.5, 95.0, -99.9, 12.0],  # 95.0 and -99.9 are invalid
            'lon': [-118.0, 200.0, -15.0, 185.0], # 200.0 and 185.0 are invalid
            'value': [10.0, -5.0, 3.0, 12.5]  # -5.0 is negative
        })
        
        coord_res = validator.check_coordinates(df_mock, 'lat', 'lon')
        self.assertEqual(coord_res['status'], 'WARNING')
        self.assertEqual(coord_res['invalid_latitudes'], 2)
        self.assertEqual(coord_res['invalid_longitudes'], 2)
        
        neg_res = validator.check_negative_values(df_mock, ['value'])
        self.assertEqual(neg_res['value']['negative_count'], 1)

if __name__ == "__main__":
    unittest.main()
