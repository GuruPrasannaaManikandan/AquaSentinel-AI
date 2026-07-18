# Reproducibility Report

This document records configurations and seeds to ensure 100% reproducibility of the machine learning baseline training.

## 1. Pinned Seeds
- **Global Project Seed:** 42
- **scikit-learn Random State:** Pinned to 42 across all models (LogisticRegression, DecisionTree, RandomForest, HistGradientBoosting).

## 2. Software Versions
- Python: standard runtime
- Scikit-learn: >= 1.2.0
- Pandas: >= 2.0.0
- NumPy: >= 1.24.0

## 3. Data Split Metadata Verification
Staged data partitions in `data/processed/` are derived using chronological splitting and remain identical across experiment execution runs.
