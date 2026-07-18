import numpy as np

def validate_inputs(u, v):
    """
    Validates that inputs are numpy arrays, contain only finite values,
    and have compatible dimensionalities.
    """
    u = np.asarray(u)
    v = np.asarray(v)

    if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)):
        raise ValueError("Inputs contain non-finite values (NaNs or Infinite values).")

    # Check dimension matching on the last axis
    u_dim = u.shape[-1]
    v_dim = v.shape[-1]
    if u_dim != v_dim:
        raise ValueError(f"Dimensionality mismatch on the last axis: {u_dim} vs {v_dim}")
        
    return u, v

def euclidean_distance(u, v):
    """
    Calculates the Euclidean distance between u and v.
    Supports NumPy broadcasting:
    - If u is (D,) and v is (N, D), returns array of shape (N,)
    - If u is (M, D) and v is (N, D), returns array of shape (M, N)
    """
    u, v = validate_inputs(u, v)
    
    if len(u.shape) == 2 and len(v.shape) == 2:
        # Pairwise distance matrix calculation
        return np.sqrt(np.sum((u[:, np.newaxis, :] - v[np.newaxis, :, :]) ** 2, axis=-1))
    
    return np.sqrt(np.sum((u - v) ** 2, axis=-1))

def manhattan_distance(u, v):
    """
    Calculates the Manhattan (L1 / city block) distance between u and v.
    Supports NumPy broadcasting:
    - If u is (D,) and v is (N, D), returns array of shape (N,)
    - If u is (M, D) and v is (N, D), returns array of shape (M, N)
    """
    u, v = validate_inputs(u, v)
    
    if len(u.shape) == 2 and len(v.shape) == 2:
        return np.sum(np.abs(u[:, np.newaxis, :] - v[np.newaxis, :, :]), axis=-1)
        
    return np.sum(np.abs(u - v), axis=-1)

def get_distance_metric(metric_name):
    """
    Retrieves the distance function by its string identifier.
    """
    name = metric_name.lower().strip()
    if name in ["euclidean", "l2"]:
        return euclidean_distance
    elif name in ["manhattan", "l1", "cityblock"]:
        return manhattan_distance
    else:
        raise ValueError(f"Unknown affinity metric: '{metric_name}'. Supported metrics: 'euclidean', 'manhattan'.")
