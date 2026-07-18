# Dataset Compatibility Assessment

This document assesses whether the CAML Cyanobacteria Abundance dataset and the HABSOS Harmful Algal Bloom dataset can be merged, or if they should remain independent components in a multi-model architecture.

## Comparison Summary

| Metric / Dimension | CAML Dataset | HABSOS Dataset |
| --- | --- | --- |
| **Target Organism** | Cyanobacteria (Blue-green algae, multiple genera) | *Karenia brevis* (Dinoflagellate) |
| **Water Ecosystem** | Inland / Freshwater (Lakes, rivers, reservoirs) | Marine / Coastal Saltwater |
| **Geographic Span** | Contiguous United States (Lat: 26.39 to 48.97) | Gulf of Mexico (Lat: 24.00 to 30.71) |
| **Temporal Span** | 2013-01-04 to 2021-12-29 | 1953-08-19 to 2024-03-25 |
| **Primary Predictor** | Abundance / distance to water | Cell counts, water salinity, water temp |
| **Target Structure** | Integer severity level (1-5) | Categorical level (not observed to high) / numeric cell count |

## Assessment Results

1. **Direct Merging Feasibility:**
   - **Scientifically Incorrect:** Cyanobacteria thrives in freshwater ecosystems, whereas *Karenia brevis* is a marine organism that grows in highly saline environments. Concatenating them into a single tabular file would force models to learn conflicting physical thresholds (e.g. salinity ~35 PPT triggers red tide blooms, but kills cyanobacteria; temperature thresholds differ).
   - **Feature Incongruence:** HABSOS features detailed marine parameters (`SALINITY` and `WATER_TEMP`), while CAML features geographical buffers like `distance_to_water_m`. Merging would result in ~50% missing fields for all records.

2. **Recommended Decision Support Architecture:**
   - **Multi-Model Routing Architecture:** Keep the models separate.
   - **Model A (Freshwater Cyanobacteria Model):** Trained on CAML. Predicts cyanobacteria severity based on geographical inputs, month, and water distance.
   - **Model B (Marine Harmful Algal Bloom Model):** Trained on HABSOS. Predicts red tide probability and category based on latitude, longitude, salinity, temperature, and depth.
   - **IoT Gateway Routing Logic:** The virtual IoT sensor nodes feed temperature, pH, salinity, and turbidity. When the backend receives sensor readings, it evaluates the **Salinity** level:
     - **Salinity < 5 PPT (Freshwater):** Invokes Model A.
     - **Salinity >= 5 PPT (Saltwater/Marine):** Invokes Model B.
     - **This routing mechanism achieves a modular, scientifically clean, and physically sound prediction system.**
