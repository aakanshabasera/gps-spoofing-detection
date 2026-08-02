import numpy as np
import pandas as pd
from typing import Tuple
from sklearn.ensemble import IsolationForest
from .feature_engineering import FeatureEngineeringPipeline


class IsolationForestAnomalyDetector:
    """
    Unsupervised Isolation Forest Anomaly Detector.
    Trains on normal telemetry features and scores test observations for statistical anomalies.
    """

    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        self.model = IsolationForest(contamination=contamination, random_state=random_state)
        self.is_trained = False

    def fit(self, features_df: pd.DataFrame):
        """Trains Isolation Forest on clean baseline feature data."""
        if features_df.empty:
            return
        self.model.fit(features_df)
        self.is_trained = True

    def predict_anomaly_scores(self, features_df: pd.DataFrame) -> np.ndarray:
        """
        Returns normalized anomaly scores in range [0.0, 100.0] where 100.0 indicates high anomaly.
        """
        if not self.is_trained or features_df.empty:
            return np.zeros(len(features_df))
            
        # score_samples returns negative anomaly score (lower means more anomalous)
        raw_scores = self.model.score_samples(features_df)
        
        # Scale to 0-100 range
        min_s = raw_scores.min()
        max_s = raw_scores.max()
        if max_s - min_s > 1e-6:
            norm_scores = (max_s - raw_scores) / (max_s - min_s) * 100.0
        else:
            norm_scores = np.zeros_like(raw_scores)
            
        return np.round(norm_scores, 1)
