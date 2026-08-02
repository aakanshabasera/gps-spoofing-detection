import uuid
import yaml
import os
from typing import List, Dict, Any, Optional
import pandas as pd
from geopy.distance import geodesic


class ImpossibleSpeedDetector:
    """
    Rule-based detector evaluating reported GPS position movement for physically impossible speeds.
    Uses geodesic distance calculations across consecutive observations.
    """

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "config", "thresholds.yaml")
        
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {
                "kinematic_limits": {
                    "aircraft": {"max_airborne_speed_kts": 600.0, "max_ground_speed_kts": 180.0},
                    "ground_vehicle": {"max_speed_kts": 45.0}
                }
            }

    def detect(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Analyzes trajectory DataFrame sorted by asset_id and timestamp.
        Returns a list of structured alert dictionaries for observations exceeding speed limits.
        """
        alerts: List[Dict[str, Any]] = []
        if df.empty or len(df) < 2:
            return alerts
        
        # Sort by asset and timestamp
        sorted_df = df.sort_values(by=["asset_id", "timestamp"]).reset_index(drop=True)
        
        for idx in range(1, len(sorted_df)):
            prev_row = sorted_df.iloc[idx - 1]
            curr_row = sorted_df.iloc[idx]
            
            # Ensure same asset
            if prev_row["asset_id"] != curr_row["asset_id"]:
                continue
            
            dt_sec = float(curr_row["timestamp"] - prev_row["timestamp"])
            if dt_sec <= 0:
                continue
            
            # Calculate geodesic distance in meters
            point_prev = (prev_row["latitude"], prev_row["longitude"])
            point_curr = (curr_row["latitude"], curr_row["longitude"])
            distance_m = geodesic(point_prev, point_curr).meters
            
            # Computed instantaneous speed
            calc_speed_ms = distance_m / dt_sec
            calc_speed_kts = calc_speed_ms / 0.514444
            
            asset_type = curr_row.get("asset_type", "aircraft")
            alt_ft = curr_row.get("altitude_ft", 0.0)
            
            # Determine threshold based on flight phase (ground vs airborne)
            if asset_type == "aircraft":
                limit_kts = self.config["kinematic_limits"]["aircraft"]["max_ground_speed_kts"] if alt_ft <= 5.0 else self.config["kinematic_limits"]["aircraft"]["max_airborne_speed_kts"]
            else:
                limit_kts = self.config["kinematic_limits"]["ground_vehicle"]["max_speed_kts"]
            
            # Flag impossible speed anomaly
            if calc_speed_kts > limit_kts:
                alert = {
                    "alert_id": str(uuid.uuid4()),
                    "timestamp": curr_row["timestamp"],
                    "asset_id": curr_row["asset_id"],
                    "asset_type": asset_type,
                    "alert_type": "IMPOSSIBLE_SPEED",
                    "severity": "CRITICAL",
                    "risk_score": 85.0,
                    "confidence": 0.95,
                    "location": (curr_row["latitude"], curr_row["longitude"]),
                    "detected_indicators": [
                        f"Calculated speed of {calc_speed_kts:.1f} kts ({calc_speed_ms:.1f} m/s) exceeds max limit of {limit_kts:.1f} kts.",
                        f"Instantaneous displacement: {distance_m:.1f} meters over {dt_sec:.1f} seconds."
                    ],
                    "expected_position": (prev_row["latitude"], prev_row["longitude"]),
                    "reported_position": (curr_row["latitude"], curr_row["longitude"]),
                    "explanation": f"GPS SPOOFING SUSPECTED: Impossible movement speed of {calc_speed_kts:.1f} kts detected for asset {curr_row['asset_id']}.",
                    "status": "NEW"
                }
                alerts.append(alert)
                
        return alerts
