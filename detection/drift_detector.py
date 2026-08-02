import math
import uuid
from typing import List, Dict, Any
import pandas as pd
from geopy.distance import geodesic


class GradualDriftDetector:
    """
    Detects gradual GPS trajectory drift by comparing reported position with projected kinematic trajectory.
    """

    def __init__(self, max_deviation_m: float = 50.0):
        self.max_deviation_m = max_deviation_m

    def detect(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        alerts: List[Dict[str, Any]] = []
        if df.empty or len(df) < 2:
            return alerts
            
        sorted_df = df.sort_values(by=["asset_id", "timestamp"]).reset_index(drop=True)
        
        for idx in range(1, len(sorted_df)):
            prev_row = sorted_df.iloc[idx - 1]
            curr_row = sorted_df.iloc[idx]
            
            if prev_row["asset_id"] != curr_row["asset_id"]:
                continue
                
            dt_sec = float(curr_row["timestamp"] - prev_row["timestamp"])
            if dt_sec <= 0:
                continue
                
            prev_speed_ms = float(prev_row.get("speed_kts", 0.0)) * 0.514444
            prev_heading_rad = math.radians(float(prev_row.get("heading_deg", 0.0)))
            
            # Kinematic position projection
            dist_m = prev_speed_ms * dt_sec
            exp_lat = prev_row["latitude"] + (dist_m * math.cos(prev_heading_rad)) / 111_000.0
            exp_lon = prev_row["longitude"] + (dist_m * math.sin(prev_heading_rad)) / 97_000.0
            
            rep_point = (curr_row["latitude"], curr_row["longitude"])
            exp_point = (exp_lat, exp_lon)
            
            deviation_m = geodesic(rep_point, exp_point).meters
            
            if deviation_m > self.max_deviation_m:
                alert = {
                    "alert_id": str(uuid.uuid4()),
                    "timestamp": curr_row["timestamp"],
                    "asset_id": curr_row["asset_id"],
                    "asset_type": curr_row.get("asset_type", "aircraft"),
                    "alert_type": "GRADUAL_DRIFT",
                    "severity": "HIGH",
                    "risk_score": 65.0,
                    "confidence": 0.85,
                    "location": rep_point,
                    "detected_indicators": [
                        f"Trajectory deviation of {deviation_m:.1f} meters from projected path over {dt_sec:.1f}s."
                    ],
                    "expected_position": (round(exp_lat, 6), round(exp_lon, 6)),
                    "reported_position": rep_point,
                    "explanation": f"GRADUAL DRIFT DETECTED: Asset {curr_row['asset_id']} deviated {deviation_m:.1f}m from expected path.",
                    "status": "NEW"
                }
                alerts.append(alert)
                
        return alerts
