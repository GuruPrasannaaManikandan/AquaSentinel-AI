import os
import time
import joblib
import json
import logging
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from src.utils.config import Config
from src.models.evaluate import calculate_classification_metrics

logger = logging.getLogger("aquatic_ais.train")

def get_classifier(model_name, params, seed=42, use_class_weights=False):
    """
    Instantiates the correct classifier class with parameters and class weighting configurations.
    """
    logger.info(f"Instantiating classifier: {model_name} with params {params}")
    
    # Check for class weights
    weight = "balanced" if use_class_weights else None

    if model_name == "dummy":
        return DummyClassifier(strategy="stratified", random_state=seed)
        
    elif model_name == "logistic_regression":
        return LogisticRegression(
            C=params.get("C", 1.0),
            max_iter=params.get("max_iter", 1000),
            multi_class=params.get("multi_class", "multinomial"),
            solver=params.get("solver", "lbfgs"),
            class_weight=weight,
            random_state=seed
        )
        
    elif model_name == "decision_tree":
        return DecisionTreeClassifier(
            max_depth=params.get("max_depth", 8),
            min_samples_split=params.get("min_samples_split", 5),
            criterion=params.get("criterion", "gini"),
            class_weight=weight,
            random_state=seed
        )
        
    elif model_name == "random_forest":
        return RandomForestClassifier(
            n_estimators=params.get("n_estimators", 100),
            max_depth=params.get("max_depth", 12),
            min_samples_split=params.get("min_samples_split", 5),
            class_weight=weight,
            n_jobs=params.get("n_jobs", -1),
            random_state=seed
        )
        
    elif model_name == "hist_gradient_boosting":
        # HistGradientBoostingClassifier supports class_weight starting in v1.2
        # We try to apply it, otherwise ignore or handle via parameter
        return HistGradientBoostingClassifier(
            max_iter=params.get("max_iter", 100),
            max_depth=params.get("max_depth", 8),
            learning_rate=params.get("learning_rate", 0.1),
            class_weight=weight,
            random_state=seed
        )
        
    else:
        raise ValueError(f"Unknown model architecture type: {model_name}")


def train_model_pipeline(model_name, classifier, preprocessor, X_train, y_train, X_val, y_val):
    """
    Wraps preprocessor and classifier inside a single pipeline, fits it, and evaluates performance.
    """
    logger.info(f"Training unified pipeline for {model_name}...")
    
    # Construct combined pipeline
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', classifier)
    ])

    # Time fitting
    start_time = time.time()
    pipeline.fit(X_train, y_train)
    fit_duration = time.time() - start_time
    logger.info(f"Model {model_name} successfully trained in {fit_duration:.4f} seconds.")

    # Time inference
    start_inf = time.time()
    y_val_pred = pipeline.predict(X_val)
    inf_duration = (time.time() - start_inf) / len(X_val)
    
    # Evaluate
    y_train_pred = pipeline.predict(X_train)
    
    train_metrics = calculate_classification_metrics(y_train, y_train_pred)
    val_metrics = calculate_classification_metrics(y_val, y_val_pred)
    
    return pipeline, {
        'model_name': model_name,
        'fit_duration_sec': fit_duration,
        'inference_duration_per_row_sec': inf_duration,
        'train_metrics': train_metrics,
        'val_metrics': val_metrics
    }
