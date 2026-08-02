import uuid
from typing import List, Dict, Any
import pandas as pd
from geospatial.airport_map import AirportMap


class GeofenceDetector:
    """
    Detects unauthorized positions outside the airport geospatial boundary.
    """

    def __init__(self, airport_map: AirportMap):
        self.airport_map = airport_map

    def detect(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        alerts: List[Dict[str, Any]] = []
        if df.empty:
            return alerts
            
        for _, row in df.iterrows():
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            alt_ft = float(row.get("altitude_ft", 0.0))
            asset_type = row.get("asset_type", "aircraft")
            
            # Ground vehicles or aircraft on ground should be inside boundary
            if alt_ft <= 50.0 or asset_type == "ground_vehicle":
                inside = self.airport_map.is_inside_airport_boundary(lat, lon)
                if not inside:
                    alerts.append({
                        "alert_id": str(uuid.uuid4()),
                        "timestamp": row["timestamp"],
                        "asset_id": row["asset_id"],
                        "asset_type": asset_type,
                        "alert_type": "GEOFENCE_VIOLATION",
                        "severity": "HIGH",
                        "risk_score": 70.0,
                        "confidence": 0.90,
                        "location": (lat, lon),
                        "detected_indicators": [f"Position ({lat:.6f}, {lon:.6f}) is outside airport boundary polygon."],
                        "expected_position": (self.airport_map.gdf.iloc[0].geometry.centroid.y, self.airport_map.gdf.iloc[0].geometry.centroid.x),
                        "reported_position": (lat, lon),
                        "explanation": f"GEOFENCE VIOLATION: Asset {row['asset_id']} reported position outside airport perimeter boundary.",
                        "status": "NEW"
                    })
        return alerts
