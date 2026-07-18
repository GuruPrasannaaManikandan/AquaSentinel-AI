# Missing-Data Analysis Report (HABSOS)

This report investigates the missingness structure of water temperature and salinity features in the HABSOS dataset, determining the mechanism of missingness, and justifying our custom Group-Based Median Imputation strategy.

---

## 1. Missingness Overview
The two vital continuous physical predictors in the HABSOS dataset have substantial missingness rates:
- **`WATER_TEMP`:** $49.62\%$ missing (105,110 null values out of 211,834).
- **`SALINITY`:** $48.97\%$ missing (103,736 null values out of 211,834).
- **`WIND_DIR` & `WIND_SPEED`:** $>99\%$ missing. (Dropping is the only viable strategy).
- **`SAMPLE_DEPTH`:** $2.60\%$ missing. Per HABSOS scientific protocol, a missing depth indicates a sample collected near the water surface. We will impute these with $0.0$ meters.

---

## 2. Temporal & Regional Missingness Analysis

### Missingness by Year:
Our historical data audit shows that missingness is heavily correlated with the year of sample collection:
- **Before 1990:** $>80\%$ of observations are missing both salinity and water temperature. Environmental sensors were not widely deployed or standardized.
- **2010–2024:** Missingness rates drop to $<20\%$ as modern multi-parameter probes became standard field equipment.
- **Conclusion:** The missingness is **MAR (Missing At Random)** rather than **MCAR (Missing Completely At Random)** because the probability of missingness is strongly dependent on the observable variable **Year**.

### Missingness by Location (State):
- Mississippi (MS) and Alabama (AL) records have higher rates of missing salinity/temp compared to Florida (FL), due to differences in state agency monitoring protocols.

---

## 3. Comparison of Imputation Strategies

We evaluated multiple methods for handling the missing 49% temperature and salinity features:

| Imputation Method | Pros | Cons | Decision |
| --- | --- | --- | --- |
| **Drop Features** | Simple, eliminates nulls. | Destroys critical environmental predictors (salinity/temp are key physics in algal growth). | **REJECT** |
| **Drop Rows** | Simple, clean. | Discards ~50% of the dataset, including critical historical bloom patterns. | **REJECT** |
| **Global Median Imputation** | Preserves all rows. | Distorts the natural physical bounds (e.g. assigning the same median temp to Florida in July and Texas in December). | **REJECT** |
| **KNN / Iterative Imputation**| Captures relationships. | Extremely slow on 211,000 rows, risk of spatial leak across folds if fit improperly. | **REJECT** |
| **Group-Based Median Imputation** | Preserves regional and seasonal physical bounds (imputes Florida-July nulls with Florida-July medians). | Requires custom transformer logic. | **RECOMMENDED** |

---

## 4. Proposed Group-Based Median Imputation Strategy

We will implement a custom scikit-learn transformer `GroupMedianImputer`:
1.  **Group Definitions:** Group the training data by `STATE_ID` and `Month` (extracted from dates).
2.  **Median Matrix:** Compute the median `SALINITY` and `WATER_TEMP` for each group.
3.  **Imputation Flow:**
    *   Find the row's `STATE_ID` and `Month`. Impute missing value with that group's median.
    *   *First Fallback:* If a group has no training values (null), use the median of the `STATE_ID`.
    *   *Second Fallback:* If still null, use the global training median of that column.
4.  **Missingness Indicator:** Add a binary column (e.g., `SALINITY_is_missing`) to let the ML model know if a value was imputed, as the fact that data was not collected might correlate with background/not observed conditions.
5.  **Leakage Safeguard:** The group medians are calculated **strictly on the training partition** and then applied to the validation and test partitions.
