import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, precision_recall_fscore_support, 
    cohen_kappa_score, matthews_corrcoef, confusion_matrix
)
import os
import logging

logger = logging.getLogger("aquatic_ais.evaluate")

def calculate_classification_metrics(y_true, y_pred):
    """
    Computes a wide array of classification performance metrics.
    """
    accuracy = accuracy_score(y_true, y_pred)
    balanced_acc = balanced_accuracy_score(y_true, y_pred)
    cohen_kappa = cohen_kappa_score(y_true, y_pred)
    mcc = matthews_corrcoef(y_true, y_pred)
    
    # Calculate macro and weighted precision, recall, F1
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, average='macro', zero_division=0
    )
    precision_w, recall_w, f1_w, _ = precision_recall_fscore_support(
        y_true, y_pred, average='weighted', zero_division=0
    )

    # Calculate per-class metrics
    classes = np.unique(y_true)
    precision_per, recall_per, f1_per, support = precision_recall_fscore_support(
        y_true, y_pred, average=None, labels=classes, zero_division=0
    )
    
    per_class_metrics = {}
    for idx, cls in enumerate(classes):
        per_class_metrics[str(cls)] = {
            'precision': float(precision_per[idx]),
            'recall': float(recall_per[idx]),
            'f1_score': float(f1_per[idx]),
            'support': int(support[idx])
        }

    return {
        'accuracy': float(accuracy),
        'balanced_accuracy': float(balanced_acc),
        'precision_macro': float(precision_macro),
        'recall_macro': float(recall_macro),
        'f1_macro': float(f1_macro),
        'f1_weighted': float(f1_w),
        'cohen_kappa': float(cohen_kappa),
        'mcc': float(mcc),
        'per_class': per_class_metrics
    }

def plot_confusion_matrix(y_true, y_pred, classes, output_path, title="Confusion Matrix", normalize=False):
    """
    Generates and saves a confusion matrix heatmap using seaborn.
    """
    cm = confusion_matrix(y_true, y_pred, labels=classes)
    
    plt.figure(figsize=(8, 6))
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        cm = np.nan_to_num(cm) # replace NaNs with 0
        sns.heatmap(cm, annot=True, fmt=".2f", cmap="Blues", xticklabels=classes, yticklabels=classes)
    else:
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=classes, yticklabels=classes)
        
    plt.title(title, fontsize=14)
    plt.ylabel('True Class', fontsize=12)
    plt.xlabel('Predicted Class', fontsize=12)
    plt.tight_layout()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved confusion matrix plot to: {output_path}")

def analyze_dangerous_false_negatives(y_true, y_pred, dangerous_classes, normal_classes):
    """
    Audits predictions to measure severe false-negative rates.
    Specifically calculates:
    1. How many dangerous observations are predicted as normal.
    2. False Negative Rate (FNR) on dangerous classes.
    3. Recall of dangerous classes.
    """
    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)
    
    # Find indices of true dangerous samples
    dangerous_mask = np.isin(y_true_arr, dangerous_classes)
    total_dangerous = int(dangerous_mask.sum())
    
    if total_dangerous == 0:
        return {
            'total_dangerous': 0,
            'predicted_as_normal': 0,
            'dangerous_recall': 0.0,
            'dangerous_fnr': 0.0
        }
        
    # How many of these true dangerous samples are predicted as normal?
    predicted_normal = int(np.isin(y_pred_arr[dangerous_mask], normal_classes).sum())
    
    # Recall = TP / (TP + FN) on dangerous classes.
    # Here, a true positive is predicting a dangerous sample as ANY of the dangerous classes.
    tp = int(np.isin(y_pred_arr[dangerous_mask], dangerous_classes).sum())
    dangerous_recall = tp / total_dangerous
    dangerous_fnr = 1.0 - dangerous_recall

    return {
        'total_dangerous': total_dangerous,
        'predicted_as_normal': predicted_normal,
        'dangerous_recall': float(dangerous_recall),
        'dangerous_fnr': float(dangerous_fnr)
    }
