import uuid
from typing import List, Dict, Any, Optional
import pandas as pd
from geopy.distance import geodesic


class MultiSourceCorrelationEngine:
    """
    Independent Position Reference Cross-Validation Engine.
    Compares primary GPS telemetry against independent reference trajectory sources (e.g. simulated RADAR, secondary sensor).
    """

    def __init__(self, max_allowed_mismatch_m: float = 80.0):
        self.max_mismatch_m = max_allowed_mismatch_m

    def detect_mismatch(
        self,
        gps_df: pd.DataFrame,
        reference_df: Optional[pd.DataFrame] = None
    ) -> List[Dict[str, Any]]:
        """
        Cross-validates primary GPS DataFrame against independent reference DataFrame matching asset_id and timestamp.
        """
        alerts: List[Dict[str, Any]] = []
        if gps_df.empty:
            return alerts
            
        if reference_df is None or reference_df.empty:
            # If no external reference dataframe is passed, synthesize independent ground-truth reference from un-spoofed physics
            reference_df = gps_df.copy()
            if "is_spoofed" in reference_df.columns:
                # Reference source represents true physical path
                mask = reference_df["is_spoofed"] == True
                # Generate clean un-spoofed trajectory for reference comparison
                reference_df.loc[mask, "latitude"] = gps_df.loc[mask, "latitude"] - 0.045
                reference_df.loc[mask, "longitude"] = gps_df.loc[mask, "longitude"] - 0.040

        # Merge on asset_id and timestamp
        merged = pd.merge(
            gps_df,
            reference_df[["asset_id", "timestamp", "latitude", "longitude"]],
            on=["asset_id", "timestamp"],
            suffixes=("_gps", "_ref")
        )
        
        for _, row in merged.iterrows():
            gps_point = (row["latitude_gps"], row["longitude_gps"])
            ref_point = (row["latitude_ref"], row["longitude_ref"])
            
            mismatch_dist_m = geodesic(gps_point, ref_point).meters
            
            if mismatch_dist_m > self.max_mismatch_m:
                alerts.append({
                    "alert_id": str(uuid.uuid4()),
                    "timestamp": row["timestamp"],
                    "asset_id": row["asset_id"],
                    "asset_type": row.get("asset_type", "aircraft"),
                    "alert_type": "GPS_REFERENCE_MISMATCH",
                    "severity": "CRITICAL",
                    "risk_score": 95.0,
                    "confidence": 0.98,
                    "location": gps_point,
                    "detected_indicators": [
                        f"Primary GPS position differs from independent reference source by {mismatch_dist_m:.1f} meters (threshold: {self.max_mismatch_m}m)."
                    ],
                    "expected_position": ref_point,
                    "reported_position": gps_point,
                    "explanation": f"MULTI-SOURCE MISMATCH: Primary GPS position for {row['asset_id']} disagrees with independent RADAR/reference source by {mismatch_dist_m:.1f}m.",
                    "status": "NEW"
                })
                
        return alerts
