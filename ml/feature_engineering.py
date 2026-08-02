import math
import pandas as pd
import numpy as np
from typing import Optional
from geopy.distance import geodesic
from geospatial.airport_map import AirportMap


class FeatureEngineeringPipeline:
    """
    Transforms dynamic movement time-series into feature vectors for ML anomaly detection.
    Strictly prevents data leakage by excluding ground-truth columns (is_spoofed, scenario).
    """

    def __init__(self, airport_map: AirportMap):
        self.airport_map = airport_map

    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
            
        sorted_df = df.sort_values(by=["asset_id", "timestamp"]).copy()
        
        # Initialize feature columns
        sorted_df["calc_speed_ms"] = 0.0
        sorted_df["acceleration_ms2_feat"] = 0.0
        sorted_df["heading_change_rate"] = 0.0
        sorted_df["vertical_rate_fps"] = 0.0
        sorted_df["position_jump_distance_m"] = 0.0
        sorted_df["trajectory_deviation_m"] = 0.0
        sorted_df["dist_from_runway_m"] = 0.0
        sorted_df["dist_from_taxiway_m"] = 0.0
        sorted_df["inside_boundary"] = 1.0
        
        asset_ids = sorted_df["asset_id"].unique()
        
        for asset_id in asset_ids:
            indices = sorted_df[sorted_df["asset_id"] == asset_id].index
            
            for i in range(len(indices)):
                curr_idx = indices[i]
                lat = float(sorted_df.at[curr_idx, "latitude"])
                lon = float(sorted_df.at[curr_idx, "longitude"])
                alt_ft = float(sorted_df.at[curr_idx, "altitude_ft"])
                
                # Spatial features
                sorted_df.at[curr_idx, "dist_from_runway_m"] = self.airport_map.distance_from_runway(lat, lon)
                sorted_df.at[curr_idx, "dist_from_taxiway_m"] = self.airport_map.distance_from_taxiway(lat, lon)
                sorted_df.at[curr_idx, "inside_boundary"] = 1.0 if self.airport_map.is_inside_airport_boundary(lat, lon) else 0.0
                
                if i > 0:
                    prev_idx = indices[i - 1]
                    dt_sec = float(sorted_df.at[curr_idx, "timestamp"] - sorted_df.at[prev_idx, "timestamp"])
                    if dt_sec <= 0:
                        continue
                        
                    p_prev = (sorted_df.at[prev_idx, "latitude"], sorted_df.at[prev_idx, "longitude"])
                    p_curr = (lat, lon)
                    dist_m = geodesic(p_prev, p_curr).meters
                    
                    speed_ms = dist_m / dt_sec
                    sorted_df.at[curr_idx, "position_jump_distance_m"] = dist_m
                    sorted_df.at[curr_idx, "calc_speed_ms"] = speed_ms
                    
                    prev_speed_ms = float(sorted_df.at[prev_idx, "calc_speed_ms"])
                    sorted_df.at[curr_idx, "acceleration_ms2_feat"] = abs(speed_ms - prev_speed_ms) / dt_sec
                    
                    h1 = float(sorted_df.at[prev_idx, "heading_deg"])
                    h2 = float(sorted_df.at[curr_idx, "heading_deg"])
                    dh = abs(h2 - h1)
                    dh = min(dh, 360.0 - dh)
                    sorted_df.at[curr_idx, "heading_change_rate"] = dh / dt_sec
                    
                    prev_alt = float(sorted_df.at[prev_idx, "altitude_ft"])
                    sorted_df.at[curr_idx, "vertical_rate_fps"] = abs(alt_ft - prev_alt) / dt_sec
                    
                    # Trajectory projection deviation
                    prev_heading_rad = math.radians(h1)
                    exp_lat = sorted_df.at[prev_idx, "latitude"] + (prev_speed_ms * dt_sec * math.cos(prev_heading_rad)) / 111_000.0
                    exp_lon = sorted_df.at[prev_idx, "longitude"] + (prev_speed_ms * dt_sec * math.sin(prev_heading_rad)) / 97_000.0
                    sorted_df.at[curr_idx, "trajectory_deviation_m"] = geodesic(p_curr, (exp_lat, exp_lon)).meters

        feature_cols = [
            "calc_speed_ms",
            "acceleration_ms2_feat",
            "heading_change_rate",
            "vertical_rate_fps",
            "position_jump_distance_m",
            "trajectory_deviation_m",
            "dist_from_runway_m",
            "dist_from_taxiway_m",
            "inside_boundary"
        ]
        
        return sorted_df[feature_cols].fillna(0.0)
