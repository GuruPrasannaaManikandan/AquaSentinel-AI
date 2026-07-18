import pandas as pd
import numpy as np
import logging

logger = logging.getLogger("aquatic_ais.validation")

class DatasetValidator:
    """
    Validates structural integrity, coordinate boundaries, data types, 
    and logical bounds of aquatic datasets.
    """
    def __init__(self, name="Dataset"):
        self.name = name

    def check_nulls(self, df: pd.DataFrame) -> dict:
        """
        Calculates null counts and percentages for each column.
        """
        null_counts = df.isnull().sum()
        null_pcts = (null_counts / len(df)) * 100
        
        results = {}
        for col in df.columns:
            results[col] = {
                'null_count': int(null_counts[col]),
                'null_pct': float(null_pcts[col])
            }
        return results

    def check_duplicates(self, df: pd.DataFrame, subset=None) -> int:
        """
        Checks for duplicate rows.
        """
        dup_count = int(df.duplicated(subset=subset).sum())
        logger.info(f"[{self.name}] Found {dup_count} duplicate rows.")
        return dup_count

    def check_coordinates(self, df: pd.DataFrame, lat_col: str, lon_col: str) -> dict:
        """
        Verifies that latitude and longitude columns contain valid coordinates.
        Latitude must be in [-90, 90]. Longitude must be in [-180, 180].
        """
        if lat_col not in df.columns or lon_col not in df.columns:
            return {'status': 'ERROR', 'message': f"Coordinate columns '{lat_col}' or '{lon_col}' not found."}
            
        lats = pd.to_numeric(df[lat_col], errors='coerce')
        lons = pd.to_numeric(df[lon_col], errors='coerce')
        
        invalid_lat_mask = (lats < -90) | (lats > 90) | lats.isnull()
        invalid_lon_mask = (lons < -180) | (lons > 180) | lons.isnull()
        
        invalid_lat_count = int(invalid_lat_mask.sum())
        invalid_lon_count = int(invalid_lon_mask.sum())
        
        status = 'SUCCESS' if (invalid_lat_count == 0 and invalid_lon_count == 0) else 'WARNING'
        
        return {
            'status': status,
            'invalid_latitudes': invalid_lat_count,
            'invalid_longitudes': invalid_lon_count,
            'lat_min': float(lats.min()),
            'lat_max': float(lats.max()),
            'lon_min': float(lons.min()),
            'lon_max': float(lons.max())
        }

    def check_negative_values(self, df: pd.DataFrame, cols: list) -> dict:
        """
        Checks if numeric columns contain negative values which might be physically invalid
        (e.g., negative cell counts or distances).
        """
        results = {}
        for col in cols:
            if col not in df.columns:
                results[col] = {'status': 'NOT_FOUND'}
                continue
                
            vals = pd.to_numeric(df[col], errors='coerce')
            neg_count = int((vals < 0).sum())
            
            results[col] = {
                'negative_count': neg_count,
                'min_value': float(vals.min()) if not vals.isnull().all() else None,
                'max_value': float(vals.max()) if not vals.isnull().all() else None
            }
        return results

    def validate_all(self, df: pd.DataFrame, lat_col: str, lon_col: str, numeric_cols: list) -> dict:
        """
        Runs a comprehensive validation suite and returns results.
        """
        logger.info(f"Running validation checks for dataset: {self.name}")
        null_info = self.check_nulls(df)
        dup_count = self.check_duplicates(df)
        coord_info = self.check_coordinates(df, lat_col, lon_col)
        neg_info = self.check_negative_values(df, numeric_cols)
        
        return {
            'dataset_name': self.name,
            'row_count': len(df),
            'column_count': len(df.columns),
            'duplicate_count': dup_count,
            'coordinates': coord_info,
            'negatives': neg_info,
            'nulls': null_info
        }
