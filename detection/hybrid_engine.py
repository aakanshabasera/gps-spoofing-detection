import uuid
import os
import yaml
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from geospatial.airport_map import AirportMap
from detection import (
    ImpossibleSpeedDetector,
    SuddenJumpDetector,
    GradualDriftDetector,
    AccelerationAnomalyDetector,
    HeadingAnomalyDetector,
    AltitudeAnomalyDetector,
    GeofenceDetector,
    MultiSourceCorrelationEngine
)
from geospatial.runway_validator import RunwayValidator
from geospatial.taxiway_validator import TaxiwayValidator
from ml.feature_engineering import FeatureEngineeringPipeline
from ml.anomaly_detector import IsolationForestAnomalyDetector


class HybridRiskEngine:
    """
    Combines Rule-Based Detectors, Geospatial Infrastructure Validation,
    Multi-Source Reference Correlation, and ML Anomaly Scoring into a unified risk scoring engine.
    """

    def __init__(self, airport_map: AirportMap, config_path: Optional[str] = None):
        self.airport_map = airport_map
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "config", "thresholds.yaml")
            
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        self.weights = self.config["risk_scoring"]["weights"]
        
        # Rule detectors
        self.speed_det = ImpossibleSpeedDetector(config_path)
        self.jump_det = SuddenJumpDetector()
        self.drift_det = GradualDriftDetector()
        self.accel_det = AccelerationAnomalyDetector()
        self.heading_det = HeadingAnomalyDetector()
        self.alt_det = AltitudeAnomalyDetector()
        self.geofence_det = GeofenceDetector(airport_map)
        self.runway_val = RunwayValidator(airport_map)
        self.taxiway_val = TaxiwayValidator(airport_map)
        self.multi_source_engine = MultiSourceCorrelationEngine()
        
        # ML Pipeline
        self.feature_pipeline = FeatureEngineeringPipeline(airport_map)
        self.ml_detector = IsolationForestAnomalyDetector()

    def train_ml_baseline(self, normal_df: pd.DataFrame):
        """Train baseline ML model on normal dynamic movement trajectories."""
        feats = self.feature_pipeline.extract_features(normal_df)
        self.ml_detector.fit(feats)

    def analyze_trajectory(
        self,
        df: pd.DataFrame,
        reference_df: Optional[pd.DataFrame] = None
    ) -> List[Dict[str, Any]]:
        """
        Runs comprehensive hybrid risk analysis on input trajectory DataFrame.
        Returns a list of structured risk alerts with detailed explanations.
        """
        if df.empty:
            return []

        # Collect rule alerts
        raw_alerts: List[Dict[str, Any]] = []
        raw_alerts.extend(self.speed_det.detect(df))
        raw_alerts.extend(self.jump_det.detect(df))
        raw_alerts.extend(self.drift_det.detect(df))
        raw_alerts.extend(self.accel_det.detect(df))
        raw_alerts.extend(self.heading_det.detect(df))
        raw_alerts.extend(self.alt_det.detect(df))
        raw_alerts.extend(self.geofence_det.detect(df))
        raw_alerts.extend(self.runway_val.detect(df))
        raw_alerts.extend(self.taxiway_val.detect(df))
        raw_alerts.extend(self.multi_source_engine.detect_mismatch(df, reference_df))
        
        # Extract features and compute ML scores
        feats = self.feature_pipeline.extract_features(df)
        ml_scores = self.ml_detector.predict_anomaly_scores(feats)
        
        # Group alerts by (asset_id, timestamp)
        alert_map: Dict[Tuple[str, float], List[Dict[str, Any]]] = {}
        for a in raw_alerts:
            key = (a["asset_id"], a["timestamp"])
            if key not in alert_map:
                alert_map[key] = []
            alert_map[key].append(a)

        sorted_df = df.sort_values(by=["asset_id", "timestamp"]).reset_index(drop=True)
        final_alerts: List[Dict[str, Any]] = []
        
        for idx in range(len(sorted_df)):
            row = sorted_df.iloc[idx]
            asset_id = row["asset_id"]
            t = row["timestamp"]
            key = (asset_id, t)
            
            ml_score = ml_scores[idx] if idx < len(ml_scores) else 0.0
            row_alerts = alert_map.get(key, [])
            
            if not row_alerts and ml_score < 60.0:
                continue
                
            # Compute cumulative hybrid risk score
            accum_score = 0.0
            indicators = []
            alert_types = set()
            
            for a in row_alerts:
                atype = a["alert_type"]
                alert_types.add(atype)
                raw_risk = float(a.get("risk_score", 20.0))
                accum_score = max(accum_score, raw_risk)
                indicators.extend(a["detected_indicators"])
                
            if ml_score >= 65.0:
                accum_score += self.weights.get("ml_anomaly", 20)
                indicators.append(f"ML Isolation Forest anomaly score: {ml_score:.1f}/100.")
                
            final_risk_score = float(min(100.0, accum_score))
            
            # Severity mapping
            if final_risk_score >= 81:
                severity = "CRITICAL"
            elif final_risk_score >= 61:
                severity = "HIGH"
            elif final_risk_score >= 41:
                severity = "MEDIUM"
            elif final_risk_score >= 21:
                severity = "LOW"
            else:
                severity = "NORMAL"
                
            # Primary type selection priority
            priority_order = ["WRONG_ALTITUDE", "IMPOSSIBLE_SPEED", "POSITION_JUMP", "GPS_REFERENCE_MISMATCH", "GEOFENCE_VIOLATION", "OFF_TAXIWAY", "OFF_RUNWAY_TRAJECTORY", "GRADUAL_DRIFT"]
            primary_type = "ML_ANOMALY"
            for ptype in priority_order:
                if ptype in alert_types:
                    primary_type = ptype
                    break
            if primary_type == "ML_ANOMALY" and alert_types:
                primary_type = sorted(list(alert_types))[0]
            
            explanation_str = (
                f"GPS SPOOFING SUSPECTED\n"
                f"Asset: {asset_id} ({row.get('asset_type', 'aircraft')})\n"
                f"Risk Score: {final_risk_score:.0f}/100 | Severity: {severity}\n"
                f"Indicators:\n" + "\n".join([f"- {ind}" for ind in indicators])
            )
            
            final_alerts.append({
                "alert_id": str(uuid.uuid4()),
                "timestamp": t,
                "asset_id": asset_id,
                "asset_type": row.get("asset_type", "aircraft"),
                "alert_type": primary_type,
                "severity": severity,
                "risk_score": final_risk_score,
                "confidence": min(1.0, round(final_risk_score / 100.0 + 0.1, 2)),
                "location": (float(row["latitude"]), float(row["longitude"])),
                "detected_indicators": indicators,
                "expected_position": row_alerts[0]["expected_position"] if row_alerts else (row["latitude"], row["longitude"]),
                "reported_position": (float(row["latitude"]), float(row["longitude"])),
                "explanation": explanation_str,
                "status": "NEW"
            })
            
        return final_alerts
