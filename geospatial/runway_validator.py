import uuid
from typing import List, Dict, Any
import pandas as pd
from geospatial.airport_map import AirportMap


class RunwayValidator:
    """
    Validates aircraft alignment with active airport runways.
    """

    def __init__(self, airport_map: AirportMap, max_runway_distance_m: float = 60.0):
        self.airport_map = airport_map
        self.max_dist = max_runway_distance_m

    def detect(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        alerts: List[Dict[str, Any]] = []
        if df.empty:
            return alerts
            
        for _, row in df.iterrows():
            asset_type = row.get("asset_type", "aircraft")
            alt_ft = float(row.get("altitude_ft", 0.0))
            scenario = row.get("scenario", "")
            
            # Ground touchdown or final approach
            if asset_type == "aircraft" and alt_ft <= 100.0 and "approach" in scenario:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                dist_m = self.airport_map.distance_from_runway(lat, lon)
                
                if dist_m > self.max_dist:
                    alerts.append({
                        "alert_id": str(uuid.uuid4()),
                        "timestamp": row["timestamp"],
                        "asset_id": row["asset_id"],
                        "asset_type": asset_type,
                        "alert_type": "OFF_RUNWAY_TRAJECTORY",
                        "severity": "HIGH",
                        "risk_score": 75.0,
                        "confidence": 0.90,
                        "location": (lat, lon),
                        "detected_indicators": [f"Final approach position is {dist_m:.1f} meters off runway centerline (max allowed: {self.max_dist}m)."],
                        "expected_position": (lat, lon),
                        "reported_position": (lat, lon),
                        "explanation": f"RUNWAY DEVIATION: Aircraft {row['asset_id']} final approach trajectory is {dist_m:.1f}m away from valid runway.",
                        "status": "NEW"
                    })
        return alerts
