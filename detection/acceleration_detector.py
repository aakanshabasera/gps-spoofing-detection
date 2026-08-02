import uuid
from typing import List, Dict, Any
import pandas as pd


class AccelerationAnomalyDetector:
    """
    Detects unphysical acceleration / deceleration rates.
    """

    def __init__(self, max_aircraft_accel_ms2: float = 12.0, max_vehicle_accel_ms2: float = 6.0):
        self.max_aircraft_accel = max_aircraft_accel_ms2
        self.max_vehicle_accel = max_vehicle_accel_ms2

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
                
            v_prev_ms = float(prev_row.get("speed_kts", 0.0)) * 0.514444
            v_curr_ms = float(curr_row.get("speed_kts", 0.0)) * 0.514444
            
            accel = abs(v_curr_ms - v_prev_ms) / dt_sec
            asset_type = curr_row.get("asset_type", "aircraft")
            limit = self.max_aircraft_accel if asset_type == "aircraft" else self.max_vehicle_accel
            
            if accel > limit:
                alerts.append({
                    "alert_id": str(uuid.uuid4()),
                    "timestamp": curr_row["timestamp"],
                    "asset_id": curr_row["asset_id"],
                    "asset_type": asset_type,
                    "alert_type": "IMPLAUSIBLE_ACCELERATION",
                    "severity": "HIGH",
                    "risk_score": 60.0,
                    "confidence": 0.85,
                    "location": (curr_row["latitude"], curr_row["longitude"]),
                    "detected_indicators": [f"Acceleration rate of {accel:.2f} m/s² exceeds limit of {limit:.1f} m/s²."],
                    "expected_position": (prev_row["latitude"], prev_row["longitude"]),
                    "reported_position": (curr_row["latitude"], curr_row["longitude"]),
                    "explanation": f"ACCELERATION ANOMALY: Asset {curr_row['asset_id']} exhibited unphysical acceleration of {accel:.2f} m/s².",
                    "status": "NEW"
                })
        return alerts
