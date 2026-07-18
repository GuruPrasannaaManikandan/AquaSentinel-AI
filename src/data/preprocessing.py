import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
import logging

logger = logging.getLogger("aquatic_ais.preprocessing")

class GroupMedianImputer(BaseEstimator, TransformerMixin):
    """
    Imputes missing values in specified columns by grouping on categorical and temporal columns
    (e.g., STATE_ID and Month). If a group is missing in train, it falls back to the state median,
    and then to the global column median. Adds a missingness indicator.
    """
    def __init__(self, target_cols: list, group_cols: list, fallback_col: str = None):
        self.target_cols = target_cols
        self.group_cols = group_cols
        self.fallback_col = fallback_col
        self.group_medians_ = {}
        self.fallback_medians_ = {}
        self.global_medians_ = {}

    def fit(self, X, y=None):
        X_df = pd.DataFrame(X)
        
        # Calculate global medians
        for col in self.target_cols:
            self.global_medians_[col] = X_df[col].median()
            # If the entire column is null, default to 0
            if pd.isna(self.global_medians_[col]):
                self.global_medians_[col] = 0.0

        # Calculate group medians
        # We group by the list of group_cols and take the median
        grouped = X_df.groupby(self.group_cols)
        for col in self.target_cols:
            medians = grouped[col].median()
            # Convert series to dict for quick lookup
            self.group_medians_[col] = medians.to_dict()

        # Calculate fallback medians (e.g. by STATE_ID only)
        if self.fallback_col:
            fallback_grouped = X_df.groupby(self.fallback_col)
            for col in self.target_cols:
                self.fallback_medians_[col] = fallback_grouped[col].median().to_dict()

        logger.info(f"GroupMedianImputer fitted successfully for columns: {self.target_cols}")
        return self

    def transform(self, X):
        X_out = X.copy()
        
        for col in self.target_cols:
            if col not in X_out.columns:
                logger.warning(f"Target column '{col}' for imputer not found. Skipping.")
                continue

            # Add missingness indicator (e.g., SALINITY_is_missing)
            indicator_col = f"{col}_is_missing"
            X_out[indicator_col] = X_out[col].isnull().astype(np.float64)

            # Impute missing values row by row
            # To optimize performance, we mask null indexes and apply group lookups
            null_mask = X_out[col].isnull()
            if null_mask.any():
                null_indices = X_out[null_mask].index
                imputed_vals = []
                
                for idx in null_indices:
                    row = X_out.loc[idx]
                    
                    # Extract grouping keys
                    group_key = tuple(row[g_col] for g_col in self.group_cols)
                    # Convert single-element tuple to scalar if only 1 group column
                    if len(group_key) == 1:
                        group_key = group_key[0]
                        
                    val = None
                    # 1. Primary Lookup: Group medians (e.g., FL in Month 7)
                    if col in self.group_medians_ and group_key in self.group_medians_[col]:
                        val = self.group_medians_[col][group_key]
                        
                    # 2. Secondary Lookup: State medians fallback (e.g., FL)
                    if (pd.isna(val) or val is None) and self.fallback_col:
                        fallback_key = row[self.fallback_col]
                        if col in self.fallback_medians_ and fallback_key in self.fallback_medians_[col]:
                            val = self.fallback_medians_[col][fallback_key]
                            
                    # 3. Tertiary Fallback: Global training median
                    if pd.isna(val) or val is None:
                        val = self.global_medians_[col]
                        
                    imputed_vals.append(val)
                
                # Write imputed values back
                X_out.loc[null_indices, col] = imputed_vals

        return X_out


class DepthImputer(BaseEstimator, TransformerMixin):
    """
    Imputes missing sample depth with 0.0 (near surface) per NOAA protocol.
    """
    def __init__(self, depth_col: str):
        self.depth_col = depth_col

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X_out = X.copy()
        if self.depth_col in X_out.columns:
            X_out[self.depth_col] = X_out[self.depth_col].fillna(0.0)
        return X_out


def build_caml_preprocessing_pipeline():
    """
    Builds the preprocessor pipeline for the CAML freshwater dataset.
    Features: lat, lon, distance_to_water_m, Year, Month_sin, Month_cos, DayOfYear_sin, DayOfYear_cos, region, Season.
    """
    # Numeric features to scale
    numeric_features = [
        'lat', 'lon', 'distance_to_water_m', 
        'Year', 'Month_sin', 'Month_cos', 'DayOfYear_sin', 'DayOfYear_cos'
    ]
    
    # Categorical features to one-hot encode
    categorical_features = ['region', 'Season']

    # Preprocessing column mapping
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='median')),
                ('scaler', StandardScaler())
            ]), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ],
        remainder='drop'  # drop identifiers, raw dates, and unneeded fields
    )
    
    return preprocessor


def build_habsos_preprocessing_pipeline():
    """
    Builds the preprocessor pipeline for the HABSOS marine dataset.
    Pipeline:
      1. Imputes depth with 0.0.
      2. Imputes salinity and temperature using GroupMedianImputer.
      3. ColumnTransformer scales numerical data and encodes categorical states.
    """
    # Numeric features to scale (after imputation)
    numeric_features = [
        'LATITUDE', 'LONGITUDE', 'SAMPLE_DEPTH', 'SALINITY', 'WATER_TEMP',
        'Year', 'Month_sin', 'Month_cos', 'DayOfYear_sin', 'DayOfYear_cos',
        'SALINITY_is_missing', 'WATER_TEMP_is_missing'
    ]
    
    # Categorical features to one-hot encode
    categorical_features = ['STATE_ID', 'Season']

    # ColumnTransformer
    col_transformer = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ],
        remainder='drop'
    )
    
    # Bundle preprocessing sequence into a Pipeline
    pipeline = Pipeline(steps=[
        ('depth_imputer', DepthImputer(depth_col='SAMPLE_DEPTH')),
        ('group_imputer', GroupMedianImputer(
            target_cols=['SALINITY', 'WATER_TEMP'], 
            group_cols=['STATE_ID', 'Month'], 
            fallback_col='STATE_ID'
        )),
        ('col_transformer', col_transformer)
    ])
    
    return pipeline
