import os
import tarfile
import shutil
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger("aquatic_ais.loaders")

class BaseDatasetLoader(ABC):
    """
    Abstract base class for dataset loaders.
    """
    def __init__(self, config):
        self.config = config
        self.raw_dir = config.get_path("raw_dir", "data/raw")
        self.interim_dir = config.get_path("interim_dir", "data/interim")

    @abstractmethod
    def extract(self):
        """Extract compressed raw data files into the interim directory."""
        pass

    @abstractmethod
    def load(self):
        """Load data from the interim directory into a pandas DataFrame."""
        pass


class CAMLLoader(BaseDatasetLoader):
    """
    Loader for the CAML Cyanobacteria Abundance Dataset.
    Parses SeaBASS file headers and extracts documentation.
    """
    def __init__(self, config):
        super().__init__(config)
        self.caml_cfg = config.get_dataset_config("caml")
        self.raw_file_name = self.caml_cfg.get("raw_file")
        self.archive_name = self.caml_cfg.get("documents_archive")
        
        # Paths
        self.raw_filepath = os.path.join(self.raw_dir, "caml", self.raw_file_name)
        self.raw_archive_path = os.path.join(self.raw_dir, "caml", self.archive_name)
        self.interim_filepath = os.path.join(self.interim_dir, "caml", self.raw_file_name)
        self.doc_extract_dir = os.path.join(self.interim_dir, "caml", "documents")

    def extract(self):
        """
        Copies the raw SeaBASS file and extracts the tgz document archive to data/interim/caml/.
        """
        logger.info("Extracting CAML dataset assets...")
        os.makedirs(os.path.dirname(self.interim_filepath), exist_ok=True)
        
        # Copy the main SeaBASS data file to interim
        if os.path.exists(self.raw_filepath):
            logger.info(f"Copying CAML data file to {self.interim_filepath}")
            shutil.copy2(self.raw_filepath, self.interim_filepath)
        else:
            raise FileNotFoundError(f"CAML raw data file not found at: {self.raw_filepath}")
            
        # Extract the documents archive
        if os.path.exists(self.raw_archive_path):
            logger.info(f"Extracting CAML documents to {self.doc_extract_dir}")
            os.makedirs(self.doc_extract_dir, exist_ok=True)
            try:
                with tarfile.open(self.raw_archive_path, "r:gz") as tar:
                    # Filter members to strip potential path traversal hazards
                    members = []
                    for member in tar.getmembers():
                        # Basic security check
                        if member.name.startswith("..") or member.name.startswith("/"):
                            logger.warning(f"Skipping unsafe archive member: {member.name}")
                            continue
                        members.append(member)
                    tar.extractall(path=self.doc_extract_dir, members=members)
                logger.info("CAML documents extracted successfully.")
            except Exception as e:
                logger.error(f"Failed to extract CAML documents: {e}")
                raise e
        else:
            logger.warning(f"CAML document archive not found at: {self.raw_archive_path}")

    def parse_header(self, filepath):
        """
        Parses a SeaBASS format file header to extract key metadata like field list,
        delimiter, and missing value placeholder.
        """
        logger.info(f"Parsing SeaBASS header from {filepath}")
        header_lines = []
        data_start_idx = 0
        missing_val = -9999.0
        delimiter = ','
        fields = []
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for idx, line in enumerate(f):
                line_stripped = line.strip()
                header_lines.append(line_stripped)
                if line_stripped.startswith('/missing='):
                    try:
                        missing_val = float(line_stripped.split('=')[1].strip())
                    except ValueError:
                        pass
                elif line_stripped.startswith('/delimiter='):
                    delim_str = line_stripped.split('=')[1].strip()
                    if delim_str == 'comma':
                        delimiter = ','
                    elif delim_str == 'tab':
                        delimiter = '\t'
                elif line_stripped.startswith('/fields='):
                    fields = line_stripped.split('=')[1].strip().split(',')
                elif line_stripped == '/end_header':
                    data_start_idx = idx + 1
                    break
                    
        return {
            'data_start_idx': data_start_idx,
            'delimiter': delimiter,
            'missing_value': missing_val,
            'fields': fields
        }

    def load(self) -> pd.DataFrame:
        """
        Loads the CAML SeaBASS data from interim, replacing missing value placeholders
        with NaN and mapping columns correctly.
        """
        if not os.path.exists(self.interim_filepath):
            logger.info("Interim CAML file not found. Running extraction first.")
            self.extract()

        # Parse header first
        header_info = self.parse_header(self.interim_filepath)
        logger.info(f"Loading CAML data using parsed header info: {header_info}")
        
        # Load CSV lines after header
        df = pd.read_csv(
            self.interim_filepath, 
            skiprows=header_info['data_start_idx'], 
            header=None, 
            delimiter=header_info['delimiter']
        )
        
        # Map fields
        fields = header_info['fields']
        if len(fields) == df.shape[1]:
            df.columns = fields
        else:
            logger.warning(f"Fields count mismatch ({len(fields)} vs {df.shape[1]}). Using parsed header fields up to column count.")
            df.columns = fields[:df.shape[1]]
            
        # Replace missing values
        missing_val = header_info['missing_value']
        df = df.replace(missing_val, np.nan)
        # Also handle potential string equivalents
        df = df.replace(str(int(missing_val)) if missing_val.is_integer() else str(missing_val), np.nan)
        df = df.replace('NA', np.nan)
        df = df.replace('NaN', np.nan)
        
        logger.info(f"CAML dataset loaded successfully. Shape: {df.shape}")
        return df


class HABSOSLoader(BaseDatasetLoader):
    """
    Loader for the HABSOS Harmful Algal Bloom Dataset.
    Extracts the tar.gz archive and loads the main HABSOS CSV dataset.
    """
    def __init__(self, config):
        super().__init__(config)
        self.habsos_cfg = config.get_dataset_config("habsos")
        self.archive_name = self.habsos_cfg.get("raw_archive")
        self.csv_member_name = self.habsos_cfg.get("csv_member")
        
        # Paths
        self.raw_archive_path = os.path.join(self.raw_dir, "habsos", self.archive_name)
        # We will extract it directly inside interim/habsos
        self.extract_dir = os.path.join(self.interim_dir, "habsos")
        self.interim_csv_path = os.path.join(self.extract_dir, self.csv_member_name)

    def extract(self):
        """
        Extracts the entire HABSOS archive to data/interim/habsos/.
        """
        if not os.path.exists(self.raw_archive_path):
            raise FileNotFoundError(f"HABSOS raw archive not found at: {self.raw_archive_path}")
            
        logger.info(f"Extracting HABSOS archive {self.raw_archive_path} to {self.extract_dir}...")
        os.makedirs(self.extract_dir, exist_ok=True)
        
        try:
            with tarfile.open(self.raw_archive_path, "r:gz") as tar:
                # Security path check
                members = []
                for member in tar.getmembers():
                    if member.name.startswith("..") or member.name.startswith("/"):
                        logger.warning(f"Skipping unsafe archive member: {member.name}")
                        continue
                    members.append(member)
                tar.extractall(path=self.extract_dir, members=members)
            logger.info("HABSOS archive extracted successfully.")
        except Exception as e:
            logger.error(f"Failed to extract HABSOS archive: {e}")
            raise e

    def load(self) -> pd.DataFrame:
        """
        Loads the main HABSOS CSV file from the interim directory.
        """
        if not os.path.exists(self.interim_csv_path):
            logger.info("Interim HABSOS CSV file not found. Running extraction first.")
            self.extract()
            
        logger.info(f"Loading HABSOS data from {self.interim_csv_path}")
        # HABSOS contains mixed data types in some columns, we specify low_memory=False
        df = pd.read_csv(self.interim_csv_path, low_memory=False)
        
        # Strip whitespaces from column names if any
        df.columns = [col.strip() for col in df.columns]
        
        logger.info(f"HABSOS dataset loaded successfully. Shape: {df.shape}")
        return df
