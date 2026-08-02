import uuid
import yaml
import os
from typing import List, Dict, Any, Optional
import pandas as pd
from geopy.distance import geodesic


class SuddenJumpDetector:
    """
    Detects sudden spatial displacement jumps over small time intervals.
    """

    def __init__(self, max_displacement_m: float = 100.0, max_interval_sec: float = 3.0):
        self.max_displacement_m = max_displacement_m
        self.max_interval_sec = max_interval_sec

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
            if 0 < dt_sec <= self.max_interval_sec:
                point_prev = (prev_row["latitude"], prev_row["longitude"])
                point_curr = (curr_row["latitude"], curr_row["longitude"])
                displacement_m = geodesic(point_prev, point_curr).meters
                
                if displacement_m > self.max_displacement_m:
                    alert = {
                        "alert_id": str(uuid.uuid4()),
                        "timestamp": curr_row["timestamp"],
                        "asset_id": curr_row["asset_id"],
                        "asset_type": curr_row.get("asset_type", "aircraft"),
                        "alert_type": "POSITION_JUMP",
                        "severity": "CRITICAL",
                        "risk_score": 85.0,
                        "confidence": 0.95,
                        "location": (curr_row["latitude"], curr_row["longitude"]),
                        "detected_indicators": [
                            f"Sudden displacement jump of {displacement_m:.1f} meters over {dt_sec:.1f} seconds."
                        ],
                        "expected_position": (prev_row["latitude"], prev_row["longitude"]),
                        "reported_position": (curr_row["latitude"], curr_row["longitude"]),
                        "explanation": f"SUDDEN POSITION JUMP: Asset {curr_row['asset_id']} jumped {displacement_m:.1f}m instantaneously.",
                        "status": "NEW"
                    }
                    alerts.append(alert)
                    
        return alerts
