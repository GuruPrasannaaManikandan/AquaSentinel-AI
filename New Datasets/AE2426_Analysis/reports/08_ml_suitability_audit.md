# Report 08: Machine Learning Suitability Audit

This report evaluates the feasibility, validity, and risks of applying Machine Learning (ML) methods to the AE2426 dataset.

## ML Suitability Audit Answers

### 1. What are the possible input features?
The potential input features are:
- The full 551-wavelength CDOM absorption coefficient ($a_g$) spectrum (300 nm to 850 nm).
- Normalized spectral features (e.g., $a_g(\lambda)$ divided by $a_g(300)$).
- Extracted optical indices: CDOM spectral slopes ($S_{275-295}$, $S_{350-400}$) and the Slope Ratio ($S_R$).
- Discrete wavelengths corresponding to common satellite bands (e.g., 412 nm, 443 nm, 490 nm).

### 2. What are the possible targets?
The potential targets are HPLC pigment concentrations, specifically:
- Total Chlorophyll-a (`Tot_Chl_a`), representing total phytoplankton biomass.
- Fucoxanthin (`Fuco`), indicating diatom abundance.
- Zeaxanthin (`Zea`), indicating cyanobacteria.
- Pigment ratios and sums (e.g., photoprotective carotenoids `PPC`, photosynthetic carotenoids `PSC`).

### 3. Are targets scientifically justified?
Yes. Developing optical proxies for phytoplankton biomass and functional groups is a standard goal in satellite oceanography and bio-optics. For example, estimating Chlorophyll-a from water color or absorption spectra is widely accepted.

### 4. How many independent samples exist?
Only **12 independent physical samples** exist in the CDOM spectral dataset. Out of these, only **11 samples** can be matched to corresponding HPLC records (since Station 12 lacks a surface HPLC match).

### 5. Is sample size sufficient?
**No. A sample size of 11 is completely insufficient** for training any supervised machine learning models. Supervised models require significantly larger datasets to generalize without overfitting.

### 6. Is class imbalance present?
Not applicable for regression. For classification, the sample size is too small to define meaningful classes or evaluate class balance.

### 7. Would supervised learning be valid?
**No, supervised learning is not valid.** Training models (e.g., Random Forests, Neural Networks, Support Vector Regressors) on 11 samples is statistically meaningless. Any high-capacity model would overfit, and validation metrics would have extremely high variance.

### 8. Would unsupervised learning be valid?
**Yes, unsupervised learning is valid and recommended.** Dimensionality reduction and clustering can help analyze the structure of the dataset and group samples based on their optical properties.

### 9. Would PCA be useful for exploratory spectral analysis?
**Yes, Principal Component Analysis (PCA) is highly useful.** It can reduce the 551-dimensional spectral space to 2 or 3 principal components that explain the major modes of variation (e.g., magnitude vs. spectral slope shape) without losing physical meaning.

### 10. Would clustering be scientifically useful?
**Yes, clustering is useful.** Algorithms like K-means or Hierarchical Clustering can group the 12 spectra to see if they naturally partition into offshore (oligotrophic) and near-shore (productive/coastal) water masses, which can then be cross-referenced with pigment profiles.

### 11. Could anomaly detection be justified?
**Yes, anomaly detection is justified.** Given the small baseline dataset, one can train a one-class classifier (e.g., One-Class SVM or Isolation Forest) or use distance-based methods to identify if new CDOM spectra are anomalous (e.g., detecting the Station 20 high-runoff coastal sample).

### 12. Could the existing AIS architecture use this modality?
**Yes.** The Capstone's Negative Selection Algorithm / Artificial Immune System (AIS) operates as an anomaly detector. It could be extended to define "self" detectors in the CDOM spectral space (or PCA-reduced space) to flag out-of-distribution (OOD) optical anomalies in real-time.

### 13. Could spectral feature extraction be useful?
**Yes.** Instead of using raw wavelengths, calculating the CDOM spectral slope ($S$) or Slope Ratio ($S_R$) reduces 551 features to 1 or 2 physically interpretable indices. $S$ is computed by fitting:
$$a_g(\lambda) = a_g(\lambda_0) \cdot e^{-S(\lambda - \lambda_0)}$$

### 14. Could wavelength selection be useful?
**Yes.** Selecting specific wavelengths (e.g., 300, 350, 412, 443 nm) avoids the extreme collinearity of adjacent 1 nm bands and lowers the feature space.

### 15. Could dimensionality reduction be useful?
**Yes.** PCA or Autoencoders can reduce 551 wavelengths to 2-3 latent dimensions, making visualization and downstream tasks (like AIS) much easier.

### 16. What leakage risks exist?
If we perform any feature scaling, PCA fit, or outlier removal on the entire dataset *before* splitting for validation, information leaks from the validation set into the training set.

### 17. What pseudoreplication risks exist?
Treating the 551 wavelength rows in a single CDOM file as independent samples is a **major pseudoreplication hazard**. Each file has 551 rows, which would result in 6,612 rows for 12 files. Treating these 6,612 rows as independent training observations violates the assumption of independence, since all 551 rows within a file represent the same physical water sample.

### 18. What validation strategy would be required?
We must use **Group K-Fold or Leave-One-Group-Out Cross-Validation**, grouping by `filename` or `station`. This ensures that all wavelength measurements from a single physical sample are kept together in either the train or validation set, preventing data leakage.

### 19. Is deep learning scientifically justified?
**No. Deep learning is completely unjustified.** Neural networks require thousands of samples to learn representations. Applying deep learning to 11 samples is bad practice.

### 20. Is classical ML scientifically justified?
Only for **unsupervised exploratory analysis** (PCA, K-means, Hierarchical Clustering) or **anomaly detection** (One-Class classification/AIS). Supervised classical ML (like PLS Regression or Ridge Regression) is only justified as a simple baseline under strict, small-sample validation constraints.

---

## Methodological Distinctions

For future work, the project must distinguish between:
1. **Exploratory Data Analysis (EDA)**: Visualizing curves and distributions (e.g., Fucoxanthin vs. Chlorophyll-a).
2. **Statistical Analysis**: Computing means, standard deviations, and checking correlation values (e.g., r = 0.93 for Fuco vs. Chl-a).
3. **Unsupervised Exploration**: PCA and clustering to identify spatial gradients (coastal vs. offshore transition).
4. **Supervised ML**: Training predictive models (not recommended due to $N=11$).
5. **Production Deployment**: Integrating models into the active dashboard or gateway (not recommended for these specific regression targets).
