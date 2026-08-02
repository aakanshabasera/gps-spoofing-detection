import uuid
from typing import List, Dict, Any
import pandas as pd
from geospatial.airport_map import AirportMap


class TaxiwayValidator:
    """
    Validates that ground support vehicles and taxiing aircraft stay within designated taxiway corridors.
    """

    def __init__(self, airport_map: AirportMap, max_taxiway_distance_m: float = 40.0):
        self.airport_map = airport_map
        self.max_dist = max_taxiway_distance_m

    def detect(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        alerts: List[Dict[str, Any]] = []
        if df.empty:
            return alerts
            
        for _, row in df.iterrows():
            asset_type = row.get("asset_type", "aircraft")
            alt_ft = float(row.get("altitude_ft", 0.0))
            
            # Ground movement
            if alt_ft <= 5.0:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                dist_taxiway = self.airport_map.distance_from_taxiway(lat, lon)
                dist_runway = self.airport_map.distance_from_runway(lat, lon)
                
                min_dist = min(dist_taxiway, dist_runway)
                
                if min_dist > self.max_dist:
                    alerts.append({
                        "alert_id": str(uuid.uuid4()),
                        "timestamp": row["timestamp"],
                        "asset_id": row["asset_id"],
                        "asset_type": asset_type,
                        "alert_type": "OFF_TAXIWAY",
                        "severity": "HIGH",
                        "risk_score": 70.0,
                        "confidence": 0.88,
                        "location": (lat, lon),
                        "detected_indicators": [f"Ground asset is {min_dist:.1f} meters off designated taxiway/runway paths."],
                        "expected_position": (lat, lon),
                        "reported_position": (lat, lon),
                        "explanation": f"OFF-TAXIWAY ANOMALY: Asset {row['asset_id']} reported position {min_dist:.1f}m away from approved airport paths.",
                        "status": "NEW"
                    })
        return alerts
