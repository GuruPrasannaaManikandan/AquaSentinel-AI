# Feature Importance & Interpretability Report

> [!IMPORTANT]
> **Scientific Caveat:**
> Feature importance indicates predictive contribution inside the model's structure; it does not prove physical causation.

---

## 1. CAML Random Forest (Weighted) Feature Importance

| Rank | Feature Index | Gini Importance Weight |
| --- | --- | --- |
| 1 | Transformed Feature Index 1 | 0.3016 |
| 2 | Transformed Feature Index 0 | 0.1857 |
| 3 | Transformed Feature Index 2 | 0.0849 |
| 4 | Transformed Feature Index 11 | 0.0796 |
| 5 | Transformed Feature Index 6 | 0.0781 |
| 6 | Transformed Feature Index 7 | 0.0729 |
| 7 | Transformed Feature Index 3 | 0.0595 |
| 8 | Transformed Feature Index 10 | 0.0447 |
| 9 | Transformed Feature Index 4 | 0.0298 |
| 10 | Transformed Feature Index 5 | 0.0168 |

---

## 2. HABSOS Random Forest (Weighted) Feature Importance

| Rank | Feature Index | Gini Importance Weight |
| --- | --- | --- |
| 1 | Transformed Feature Index 5 | 0.2156 |
| 2 | Transformed Feature Index 0 | 0.1457 |
| 3 | Transformed Feature Index 1 | 0.1409 |
| 4 | Transformed Feature Index 8 | 0.0992 |
| 5 | Transformed Feature Index 9 | 0.0833 |
| 6 | Transformed Feature Index 3 | 0.0716 |
| 7 | Transformed Feature Index 4 | 0.0589 |
| 8 | Transformed Feature Index 2 | 0.0451 |
| 9 | Transformed Feature Index 6 | 0.0306 |
| 10 | Transformed Feature Index 7 | 0.0275 |

## 3. Explaining Important Features:
- **Spatial Coordinates:** Coordinates are major predictive splits, capturing localized historical bloom hotspots.
- **Seasonality (Sin/Cos Month):** High Gini importance, reflecting that both dinoflagellate and cyanobacteria blooms occur during specific warm-month cycles.
- **Salinity/Temp:** Physical parameters in HABSOS are critical drivers for the dinoflagellate growth curve.
