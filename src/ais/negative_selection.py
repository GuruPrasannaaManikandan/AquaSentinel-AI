import numpy as np
import time
from sklearn.base import BaseEstimator, ClassifierMixin
from src.ais.affinity import get_distance_metric

class NegativeSelectionAlgorithm(BaseEstimator, ClassifierMixin):
    """
    Genuine Negative Selection Algorithm (NSA) classifier.
    Learns a representation of normal 'SELF' and generates artificial detectors to identify 'NON-SELF' antigens.
    """
    def __init__(self, num_detectors=100, self_radius=0.1, affinity_metric="euclidean",
                 max_attempts=50000, random_seed=42, batch_size=1000):
        self.num_detectors = num_detectors
        self.self_radius = self_radius
        self.affinity_metric = affinity_metric
        self.max_attempts = max_attempts
        self.random_seed = random_seed
        self.batch_size = batch_size
        self.detectors_ = None
        self.generation_stats_ = {}

    def fit(self, X, y=None):
        """
        Generates negative selection detectors that do not match the training SELF samples.
        X: array-like of shape (N_self, D), representing normalized training SELF samples.
        """
        start_time = time.time()
        X_self = np.asarray(X)
        N_self, D = X_self.shape
        
        # Set seed for reproducible detector generation
        rng = np.random.default_rng(self.random_seed)
        
        accepted_detectors = []
        candidates_generated = 0
        attempts = 0
        
        from scipy.spatial.distance import cdist
        metric_key = 'cityblock' if self.affinity_metric.lower() in ['manhattan', 'l1', 'cityblock'] else 'euclidean'
        
        while len(accepted_detectors) < self.num_detectors and attempts < self.max_attempts:
            # Batch candidate generation to leverage vectorized distance calculations
            current_batch_size = min(self.batch_size, self.max_attempts - attempts)
            candidates = rng.uniform(low=0.0, high=1.0, size=(current_batch_size, D))
            candidates_generated += current_batch_size
            attempts += current_batch_size
            
            # Compute pairwise distances between candidates and the training SELF samples
            dists = cdist(candidates, X_self, metric=metric_key)
            
            # Find the minimum distance from each candidate to any training SELF point
            min_dists = np.min(dists, axis=1)
            
            # Accept candidates where minimum distance to SELF is greater than self_radius
            keep_indices = np.where(min_dists > self.self_radius)[0]
            
            for idx in keep_indices:
                if len(accepted_detectors) < self.num_detectors:
                    accepted_detectors.append(candidates[idx])
                else:
                    break
                    
        self.detectors_ = np.array(accepted_detectors)
        duration = time.time() - start_time
        
        self.generation_stats_ = {
            "self_samples": N_self,
            "feature_dim": D,
            "candidates_generated": candidates_generated,
            "detectors_accepted": len(self.detectors_),
            "acceptance_rate": len(self.detectors_) / candidates_generated if candidates_generated > 0 else 0.0,
            "generation_time_sec": duration
        }
        
        return self

    def predict_anomaly(self, X, matching_radius=None):
        """
        Performs anomaly detection on incoming antigens.
        Returns:
          is_anomaly (ndarray of bool): True if antigen matches any detector.
          anomaly_score (ndarray of float): Scaled confidence of anomaly [0, 1].
          matched_count (ndarray of int): Number of matching detectors.
          min_dist (ndarray of float): Minimum distance to any detector.
        """
        X_antigens = np.asarray(X)
        N, D = X_antigens.shape
        
        r = matching_radius if matching_radius is not None else self.self_radius

        if self.detectors_ is None or len(self.detectors_) == 0:
            # Fallback when no detectors exist
            return np.zeros(N, dtype=bool), np.zeros(N), np.zeros(N, dtype=int), np.full(N, np.inf)

        from scipy.spatial.distance import cdist
        metric_key = 'cityblock' if self.affinity_metric.lower() in ['manhattan', 'l1', 'cityblock'] else 'euclidean'
        
        # Calculate distance matrix between antigens and detectors
        dists = cdist(X_antigens, self.detectors_, metric=metric_key)
        
        # Check matching rule: distance <= r (which defines the detector matching threshold)
        matches = dists <= r
        
        # Anomaly decision: antigen falls inside at least one detector's radius
        is_anomaly = np.any(matches, axis=1)
        
        # Number of matching detectors per antigen
        matched_count = np.sum(matches, axis=1)
        
        # Minimum distance to any detector
        min_dists = np.min(dists, axis=1)
        
        # Continuous anomaly score: ranges from 1.0 (exact match with detector center) to 0.0 (no match)
        anomaly_scores = np.where(min_dists <= r, 1.0 - (min_dists / r), 0.0)
        
        return is_anomaly, anomaly_scores, matched_count, min_dists

    def predict(self, X, matching_radius=None):
        """
        Scikit-learn compatible binary prediction.
        Returns 1 for anomaly (NON-SELF) and 0 for normal (SELF).
        """
        is_anomaly, _, _, _ = self.predict_anomaly(X, matching_radius=matching_radius)
        return is_anomaly.astype(int)

    def decision_function(self, X, matching_radius=None):
        """
        Scikit-learn compatible decision function.
        Returns continuous anomaly scores.
        """
        _, anomaly_scores, _, _ = self.predict_anomaly(X, matching_radius=matching_radius)
        return anomaly_scores
