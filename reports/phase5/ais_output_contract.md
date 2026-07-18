# AIS Output Contract

This document defines the formal output contract for the unsupervised Artificial Immune System (AIS) anomaly-detection layer.

---

## 1. Schema Definition
The AIS output is returned as a JSON object nested under the `"ais"` key:

```json
{
    "ais": {
        "is_anomaly": true,
        "anomaly_score": 0.82,
        "matched_detector_count": 4,
        "nearest_detector_distance": 0.13,
        "ais_version": "NSA-CAML-v1"
    }
}
```

### Field Descriptions

| Field | Type | Unit / Range | Description |
| :--- | :--- | :--- | :--- |
| **`is_anomaly`** | boolean | `true` or `false` | Anomaly decision. Determined by the NSA matching rule: `true` if the antigen matches at least one detector, `false` otherwise. |
| **`anomaly_score`** | float | `[0.0, 1.0]` | Continuous index representing the anomaly magnitude. A value of `1.0` denotes an exact match with a detector center; `0.0` denotes no match (normal SELF conditions). |
| **`matched_detector_count`** | integer | $\ge 0$ | The number of distinct generated detectors that were triggered by the antigen. |
| **`nearest_detector_distance`** | float | $\ge 0.0$ | The minimum distance (Euclidean or Manhattan depending on configuration) from the antigen to any accepted detector. If no detectors exist, defaults to `999.0`. |
| **`ais_version`** | string | SemVer string | The active model and version identifier (e.g. `'NSA-CAML-v1'`). |

---

## 2. Mathematical Score Formulation
Let the distance function be $d(a, d_j)$ between the input antigen $a$ and detector $d_j$.
Let the matching radius (equivalent to the generator's `self_radius`) be $r$.

The minimum distance to any detector is:
$$d_{\min} = \min_{j} d(a, d_j)$$

The anomaly score $S(a)$ is defined as:
$$S(a) = \begin{cases} 
1.0 - \frac{d_{\min}}{r} & \text{if } d_{\min} \le r \\
0.0 & \text{if } d_{\min} > r
\end{cases}$$

This continuous score aligns with biological immune responses, where higher affinity (closer match to a non-self detector) yields a stronger activation signal.
