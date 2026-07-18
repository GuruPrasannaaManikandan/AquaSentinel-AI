import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
import logging

logger = logging.getLogger("aquatic_ais.feature_engineering")

class TemporalFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    A custom scikit-learn transformer that extracts temporal features from date columns.
    It parses both yyyymmdd integers (CAML) and yyyy-mm-dd strings (HABSOS).
    Generates Year, Month, DayOfYear, Season, and cyclic encodings.
    """
    def __init__(self, date_col: str, date_format: str = None):
        self.date_col = date_col
        self.date_format = date_format

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # Create copy to avoid modifying original dataframe (prevent SettingWithCopyWarning)
        X_out = X.copy()
        
        if self.date_col not in X_out.columns:
            logger.warning(f"Date column '{self.date_col}' not found. Skipping temporal extraction.")
            return X_out

        logger.info(f"Extracting temporal features from column: {self.date_col}")
        
        # Convert date to datetime object
        if self.date_format == "yyyymmdd":
            # For CAML: date is numeric (e.g. 20180514)
            dates = pd.to_datetime(X_out[self.date_col], format='%Y%m%d', errors='coerce')
        else:
            # Automatic parsing for standard formats (HABSOS: 2024-04-30)
            dates = pd.to_datetime(X_out[self.date_col], errors='coerce')
            
        # Fallback default for unparseable dates: fill with a default date
        if dates.isnull().any():
            default_date = pd.Timestamp('2018-06-15')
            logger.warning(f"Unparseable dates found in '{self.date_col}'. Filling missing dates with fallback: {default_date}")
            dates = dates.fillna(default_date)

        # Extract features
        X_out['Year'] = dates.dt.year.astype(np.float64)
        X_out['Month'] = dates.dt.month.astype(np.float64)
        X_out['DayOfYear'] = dates.dt.dayofyear.astype(np.float64)
        
        # Season classification:
        # Winter = 12, 1, 2; Spring = 3, 4, 5; Summer = 6, 7, 8; Autumn = 9, 10, 11
        X_out['Season'] = dates.dt.month.map(lambda m: 
            'Winter' if m in [12, 1, 2] else
            'Spring' if m in [3, 4, 5] else
            'Summer' if m in [6, 7, 8] else 'Autumn'
        )

        # Cyclic encoding of Month (period of 12 months)
        X_out['Month_sin'] = np.sin(2 * np.pi * X_out['Month'] / 12.0)
        X_out['Month_cos'] = np.cos(2 * np.pi * X_out['Month'] / 12.0)

        # Cyclic encoding of DayOfYear (period of 365 days)
        X_out['DayOfYear_sin'] = np.sin(2 * np.pi * X_out['DayOfYear'] / 365.25)
        X_out['DayOfYear_cos'] = np.cos(2 * np.pi * X_out['DayOfYear'] / 365.25)

        return X_out
