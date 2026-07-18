# CAML Dataset Quality Audit Report

## 1. Dataset Shape & Structures
- **Name:** CAML
- **Total Rows:** 23570
- **Total Columns:** 10
- **Detected Duplicate Rows:** 0

## 2. Columns & Data Types
| Column | DataType | Null Count | Null % | Range / Unique Values |
| --- | --- | --- | --- | --- |
| uid | object | 0 | 0.0000% | 23570 unique values |
| data_provider | object | 0 | 0.0000% | 14 unique values |
| region | object | 0 | 0.0000% | 4 unique values |
| lat | float64 | 0 | 0.0000% | [26.38943, 48.97325] |
| lon | float64 | 0 | 0.0000% | [-124.1792, -67.69865] |
| date | int64 | 0 | 0.0000% | [20130104, 20211229] |
| time | object | 0 | 0.0000% | 667 unique values |
| abun | float64 | 0 | 0.0000% | [0.0, 804667.5] |
| severity | int64 | 0 | 0.0000% | [1, 5] |
| distance_to_water_m | float64 | 1 | 0.0042% | [0.0, 6468.0] |

## 3. Geographic Bounding Box
- **Latitude Bounds:** [26.38943, 48.97325]
- **Longitude Bounds:** [-124.1792, -67.69865]
- **Invalid Coordinate Formats:** 0

## 4. Class Distribution (Target Candidate: severity)
| Severity Level | Count | Percentage |
| --- | --- | --- |
| Level 1 | 9761 | 41.41% |
| Level 4 | 5824 | 24.71% |
| Level 2 | 4083 | 17.32% |
| Level 3 | 3812 | 16.17% |
| Level 5 | 90 | 0.38% |

## 5. Potential Outlier Detections
- **Abundance (cells/L) Statistics:**
  - Mean: 1266.44
  - Std Dev: 6202.46
  - Max: 804667.5 (Potential outlier check: 75th percentile is 1015.54)
  
## 6. Columns recommended to DROP in ML Modeling
- `uid`: Unique index identifier, carries no predictive information.
- `data_provider`: High cardinality categoric indicator of agency, might lead to data leakage if agencies monitor specific states.
- `date` / `time`: Dates should not be fed directly to avoid temporal sequence leakage; extract features like Month/Season instead.
