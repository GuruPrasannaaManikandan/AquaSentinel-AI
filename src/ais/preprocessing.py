import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import MinMaxScaler

class AISPreprocessor(BaseEstimator, TransformerMixin):
    """
    Dedicated AIS Preprocessing Pipeline that selects eligible environmental features,
    imputes missing values, scales features to [0, 1], and records metadata.
    Designed to prevent any data leakage.
    """
    def __init__(self, features, depth_col=None):
        self.features = features
        self.depth_col = depth_col
        self.imputer = None
        self.scaler = None
        self.metadata = {}

    def fit(self, X, y=None):
        """
        Fits imputer and scaler strictly on the training SELF (normal) dataset.
        """
        X_df = pd.DataFrame(X)
        
        # Validate that all expected features exist in the data
        missing = [f for f in self.features if f not in X_df.columns]
        if missing:
            raise ValueError(f"Features missing from input DataFrame: {missing}")

        X_feats = X_df[self.features].copy()
        
        # Impute depth with 0.0 (near surface) per NOAA protocol if applicable
        if self.depth_col and self.depth_col in X_feats.columns:
            X_feats[self.depth_col] = X_feats[self.depth_col].fillna(0.0)

        # Fit general median imputer for numeric columns
        self.imputer = SimpleImputer(strategy='median')
        self.imputer.fit(X_feats)
        
        # Transform data to fit the scaler
        X_imputed = self.imputer.transform(X_feats)
        
        # Fit MinMaxScaler to scale features to [0, 1] range
        self.scaler = MinMaxScaler()
        self.scaler.fit(X_imputed)
        
        # Compile metadata
        self.metadata = {
            "features": list(self.features),
            "depth_col": self.depth_col,
            "medians": [float(m) for m in self.imputer.statistics_],
            "min_vals": [float(m) for m in self.scaler.data_min_],
            "max_vals": [float(m) for m in self.scaler.data_max_]
        }
        return self

    def transform(self, X):
        """
        Applies learned imputation and scaling parameters to incoming antigens.
        Returns a DataFrame in the range [0, 1].
        """
        X_df = pd.DataFrame(X)
        
        # Verify schema
        missing = [f for f in self.features if f not in X_df.columns]
        if missing:
            raise ValueError(f"Features missing from input DataFrame during transform: {missing}")

        X_feats = X_df[self.features].copy()
        
        # Apply depth fallback if applicable
        if self.depth_col and self.depth_col in X_feats.columns:
            X_feats[self.depth_col] = X_feats[self.depth_col].fillna(0.0)

        # Impute missing values
        X_imputed = self.imputer.transform(X_feats)
        
        # Scale to [0, 1]
        X_scaled = self.scaler.transform(X_imputed)
        
        return pd.DataFrame(X_scaled, columns=self.features)
