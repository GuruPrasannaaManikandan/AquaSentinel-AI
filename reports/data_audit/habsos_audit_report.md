# HABSOS Dataset Quality Audit Report

## 1. Dataset Shape & Structures
- **Name:** HABSOS
- **Total Rows:** 211834
- **Total Columns:** 28
- **Detected Duplicate Rows:** 0

## 2. Columns & Data Types
| Column | DataType | Null Count | Null % | Range / Unique Values |
| --- | --- | --- | --- | --- |
| STATE_ID | object | 0 | 0.0000% | 4 unique values |
| DESCRIPTION | object | 23 | 0.0109% | 29494 unique values |
| Unnamed: 2 | float64 | 211834 | 100.0000% | [nan, nan] |
| LATITUDE | float64 | 0 | 0.0000% | [24.0, 30.7149] |
| LONGITUDE | float64 | 0 | 0.0000% | [-97.66535, -78.2789] |
| SAMPLE_DATE | object | 0 | 0.0000% | 11502 unique values |
| SAMPLE_TIME | object | 48920 | 23.0936% | 1426 unique values |
| SAMPLE_DEPTH | float64 | 5503 | 2.5978% | [0.0, 600.0] |
| GENUS | object | 0 | 0.0000% | 1 unique values |
| SPECIES | object | 0 | 0.0000% | 1 unique values |
| CATEGORY | object | 856 | 0.4041% | 5 unique values |
| CELLCOUNT | int64 | 0 | 0.0000% | [0, 388400000] |
| CELLCOUNT_UNIT | object | 0 | 0.0000% | 1 unique values |
| CELLCOUNT_QA | float64 | 192 | 0.0906% | [1.0, 9.0] |
| SALINITY | float64 | 103736 | 48.9704% | [0.0, 86.0] |
| SALINITY_UNIT | object | 103736 | 48.9704% | 1 unique values |
| SALINITY_QA | int64 | 0 | 0.0000% | [1, 9] |
| WATER_TEMP | float64 | 105110 | 49.6190% | [4.0, 39.9] |
| WATER_TEMP_UNIT | object | 105110 | 49.6190% | 1 unique values |
| WATER_TEMP_QA | int64 | 0 | 0.0000% | [1, 9] |
| WIND_DIR | float64 | 210805 | 99.5142% | [22.5, 360.0] |
| WIND_DIR_UNIT | object | 210805 | 99.5142% | 1 unique values |
| WIND_DIR_QA | int64 | 0 | 0.0000% | [5, 9] |
| WIND_SPEED | float64 | 209842 | 99.0596% | [0.0, 34.5] |
| WIND_SPEED_UNIT | object | 209842 | 99.0596% | 1 unique values |
| WIND_SPEED_QA | int64 | 0 | 0.0000% | [1, 9] |
| OBJECTID | int64 | 0 | 0.0000% | [27896, 2135994] |
| Unnamed: 27 | float64 | 211834 | 100.0000% | [nan, nan] |

## 3. Geographic Bounding Box
- **Latitude Bounds:** [24.0, 30.7149]
- **Longitude Bounds:** [-97.66535, -78.2789]
- **Invalid Coordinate Formats:** 0

## 4. Class Distribution (Target Candidate: CATEGORY / CELLCOUNT)
| Bloom Risk Category | Count | Percentage |
| --- | --- | --- |
| not observed | 164102 | 77.47% |
| very low | 18925 | 8.93% |
| low | 12567 | 5.93% |
| medium | 11705 | 5.53% |
| high | 3679 | 1.74% |
| nan | 856 | 0.40% |

## 5. Potential Outlier Detections
- **CELLCOUNT (cells/L) Statistics:**
  - Mean: 126301.01
  - Std Dev: 2210581.82
  - Max: 388400000
- **Water Salinity (PPT) Statistics:**
  - Mean: 30.88 (Null: 48.97%)
- **Water Temperature (C) Statistics:**
  - Mean: 24.77 (Null: 49.62%)

## 6. Columns recommended to DROP in ML Modeling
- `GENUS` and `SPECIES`: 100% constant value (`Karenia brevis`).
- `CELLCOUNT_UNIT`: 100% constant value (`cells/L`).
- `CELLCOUNT_QA`, `SALINITY_QA`, `WATER_TEMP_QA`, `WIND_DIR_QA`, `WIND_SPEED_QA`: Data quality flags that represent post-collection attributes.
- `OBJECTID`: Database integer index.
- `Unnamed: 2` and `Unnamed: 27`: Empty columns.
- `WIND_DIR` and `WIND_SPEED`: >99% missing data.
