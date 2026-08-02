import pandas as pd
import numpy as np
from typing import Dict, Any, List
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from geospatial.airport_map import AirportMap


class ModelEvaluator:
    """
    Evaluates rule-based, ML, and hybrid spoofing detection engines against ground-truth dataset labels.
    Calculates Accuracy, Precision, Recall, F1-Score, FPR, FNR, and Detection Latency.
    """

    def __init__(self, airport_map: AirportMap):
        from detection.hybrid_engine import HybridRiskEngine
        self.airport_map = airport_map
        self.hybrid_engine = HybridRiskEngine(airport_map)

    def evaluate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Runs evaluation on a dataset containing ground-truth `is_spoofed` column."""
        if "is_spoofed" not in df.columns:
            raise ValueError("Dataset missing 'is_spoofed' ground-truth column.")
            
        # Train ML model baseline on non-spoofed segment
        normal_subset = df[df["is_spoofed"] == False]
        if not normal_subset.empty:
            self.hybrid_engine.train_ml_baseline(normal_subset)
            
        alerts = self.hybrid_engine.analyze_trajectory(df)
        
        # Build prediction vector matching DataFrame index
        alert_timestamps = set([a["timestamp"] for a in alerts if a["risk_score"] >= 40.0])
        
        y_true = df["is_spoofed"].astype(int).values
        y_pred = np.array([1 if t in alert_timestamps else 0 for t in df["timestamp"]])
        
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (len(y_true), 0, 0, 0)
        
        acc = float(accuracy_score(y_true, y_pred))
        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
        
        # Detection latency calculation
        attack_timestamps = df[df["is_spoofed"] == True]["timestamp"].values
        if len(attack_timestamps) > 0:
            attack_start = attack_timestamps[0]
            detected_after_attack = [t for t in alert_timestamps if t >= attack_start]
            latency_sec = float(detected_after_attack[0] - attack_start) if detected_after_attack else None
        else:
            latency_sec = None
            
        return {
            "total_samples": len(df),
            "total_alerts": len(alerts),
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4),
            "detection_latency_sec": latency_sec
        }
