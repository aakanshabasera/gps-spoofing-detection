import uuid
from typing import List, Dict, Any
import pandas as pd


class AltitudeAnomalyDetector:
    """
    Detects impossible altitude variations and airborne ground vehicle anomalies.
    """

    def __init__(self, max_climb_rate_fpm: float = 6000.0, max_vehicle_alt_ft: float = 10.0):
        self.max_climb_rate_fps = max_climb_rate_fpm / 60.0 # ft/sec
        self.max_vehicle_alt_ft = max_vehicle_alt_ft

    def detect(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        alerts: List[Dict[str, Any]] = []
        if df.empty:
            return alerts
            
        sorted_df = df.sort_values(by=["asset_id", "timestamp"]).reset_index(drop=True)
        
        for idx in range(len(sorted_df)):
            curr_row = sorted_df.iloc[idx]
            asset_type = curr_row.get("asset_type", "aircraft")
            alt_ft = float(curr_row.get("altitude_ft", 0.0))
            
            # Ground vehicle altitude violation check
            if asset_type == "ground_vehicle" and alt_ft > self.max_vehicle_alt_ft:
                alerts.append({
                    "alert_id": str(uuid.uuid4()),
                    "timestamp": curr_row["timestamp"],
                    "asset_id": curr_row["asset_id"],
                    "asset_type": asset_type,
                    "alert_type": "WRONG_ALTITUDE",
                    "severity": "CRITICAL",
                    "risk_score": 90.0,
                    "confidence": 0.98,
                    "location": (curr_row["latitude"], curr_row["longitude"]),
                    "detected_indicators": [f"Ground vehicle reported airborne altitude of {alt_ft:.1f} ft."],
                    "expected_position": (curr_row["latitude"], curr_row["longitude"]),
                    "reported_position": (curr_row["latitude"], curr_row["longitude"]),
                    "explanation": f"ALTITUDE SPOOF: Ground vehicle {curr_row['asset_id']} reported impossible altitude of {alt_ft:.1f} ft.",
                    "status": "NEW"
                })
                continue
                
            if idx > 0:
                prev_row = sorted_df.iloc[idx - 1]
                if prev_row["asset_id"] != curr_row["asset_id"]:
                    continue
                    
                dt_sec = float(curr_row["timestamp"] - prev_row["timestamp"])
                if dt_sec <= 0:
                    continue
                    
                d_alt_ft = abs(alt_ft - float(prev_row.get("altitude_ft", 0.0)))
                vertical_rate_fps = d_alt_ft / dt_sec
                
                if vertical_rate_fps > self.max_climb_rate_fps:
                    alerts.append({
                        "alert_id": str(uuid.uuid4()),
                        "timestamp": curr_row["timestamp"],
                        "asset_id": curr_row["asset_id"],
                        "asset_type": asset_type,
                        "alert_type": "IMPLAUSIBLE_CLIMB_RATE",
                        "severity": "HIGH",
                        "risk_score": 75.0,
                        "confidence": 0.90,
                        "location": (curr_row["latitude"], curr_row["longitude"]),
                        "detected_indicators": [f"Vertical rate of {vertical_rate_fps*60.0:.0f} ft/min exceeds limit of {self.max_climb_rate_fps*60.0:.0f} ft/min."],
                        "expected_position": (prev_row["latitude"], prev_row["longitude"]),
                        "reported_position": (curr_row["latitude"], curr_row["longitude"]),
                        "explanation": f"VERTICAL RATE ANOMALY: Asset {curr_row['asset_id']} changed altitude by {d_alt_ft:.1f}ft in {dt_sec:.1f}s.",
                        "status": "NEW"
                    })
        return alerts
