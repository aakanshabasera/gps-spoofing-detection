import uuid
from typing import List, Dict, Any
import pandas as pd


class HeadingAnomalyDetector:
    """
    Detects unphysical heading changes taking 0°/360° boundary wraparound into account.
    """

    def __init__(self, max_rate_deg_sec: float = 20.0):
        self.max_rate = max_rate_deg_sec

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
                
            h1 = float(prev_row.get("heading_deg", 0.0))
            h2 = float(curr_row.get("heading_deg", 0.0))
            
            diff = abs(h2 - h1)
            diff = min(diff, 360.0 - diff) # Handle 0°/360° boundary
            rate = diff / dt_sec
            
            if rate > self.max_rate:
                alerts.append({
                    "alert_id": str(uuid.uuid4()),
                    "timestamp": curr_row["timestamp"],
                    "asset_id": curr_row["asset_id"],
                    "asset_type": curr_row.get("asset_type", "aircraft"),
                    "alert_type": "HEADING_ANOMALY",
                    "severity": "MEDIUM",
                    "risk_score": 45.0,
                    "confidence": 0.80,
                    "location": (curr_row["latitude"], curr_row["longitude"]),
                    "detected_indicators": [f"Heading change rate of {rate:.1f}°/s exceeds maximum threshold of {self.max_rate}°/s."],
                    "expected_position": (prev_row["latitude"], prev_row["longitude"]),
                    "reported_position": (curr_row["latitude"], curr_row["longitude"]),
                    "explanation": f"HEADING ANOMALY: Asset {curr_row['asset_id']} changed heading by {diff:.1f}° in {dt_sec:.1f}s ({rate:.1f}°/s).",
                    "status": "NEW"
                })
        return alerts
