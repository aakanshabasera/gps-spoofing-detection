import pandas as pd
import numpy as np
from typing import Tuple


class SpoofingScenarioGenerator:
    """
    Applies spoofing attack transformations to normal dynamic movement trajectories
    and maintains explicit ground-truth labels.
    """

    @staticmethod
    def inject_sudden_jump(
        df: pd.DataFrame,
        start_time_sec: float = 40.0,
        end_time_sec: float = 70.0,
        lat_offset_deg: float = 0.045, # ~5.0 km displacement jump
        lon_offset_deg: float = 0.040  # ~4.0 km displacement jump
    ) -> pd.DataFrame:
        """Injects a sudden position jump spoofing attack."""
        spoofed_df = df.copy()
        spoofed_df["scenario"] = "sudden_position_jump"
        
        mask = (spoofed_df["timestamp"] >= start_time_sec) & (spoofed_df["timestamp"] <= end_time_sec)
        spoofed_df.loc[mask, "latitude"] = (spoofed_df.loc[mask, "latitude"] + lat_offset_deg).round(6)
        spoofed_df.loc[mask, "longitude"] = (spoofed_df.loc[mask, "longitude"] + lon_offset_deg).round(6)
        spoofed_df.loc[mask, "is_spoofed"] = True
        
        return spoofed_df

    @staticmethod
    def inject_gradual_drift(
        df: pd.DataFrame,
        start_time_sec: float = 30.0,
        end_time_sec: float = 90.0,
        drift_rate_deg_per_sec: float = 0.0003 # ~33 meters/sec accumulating drift
    ) -> pd.DataFrame:
        """Injects a gradual GPS coordinate drift attack."""
        spoofed_df = df.copy()
        spoofed_df["scenario"] = "gradual_drift"
        
        for idx, row in spoofed_df.iterrows():
            t = row["timestamp"]
            if start_time_sec <= t <= end_time_sec:
                elapsed = t - start_time_sec
                lat_drift = elapsed * drift_rate_deg_per_sec
                lon_drift = elapsed * drift_rate_deg_per_sec * 0.8
                spoofed_df.at[idx, "latitude"] = round(row["latitude"] + lat_drift, 6)
                spoofed_df.at[idx, "longitude"] = round(row["longitude"] + lon_drift, 6)
                spoofed_df.at[idx, "is_spoofed"] = True
                
        return spoofed_df

    @staticmethod
    def inject_altitude_spoof(
        df: pd.DataFrame,
        start_time_sec: float = 30.0,
        end_time_sec: float = 60.0,
        fake_altitude_ft: float = 12000.0
    ) -> pd.DataFrame:
        """Injects an unphysical altitude jump (e.g. ground vehicle airborne or aircraft sudden altitude step)."""
        spoofed_df = df.copy()
        spoofed_df["scenario"] = "wrong_altitude"
        
        mask = (spoofed_df["timestamp"] >= start_time_sec) & (spoofed_df["timestamp"] <= end_time_sec)
        spoofed_df.loc[mask, "altitude_ft"] = fake_altitude_ft
        spoofed_df.loc[mask, "is_spoofed"] = True
        
        return spoofed_df

    @staticmethod
    def inject_heading_anomaly(
        df: pd.DataFrame,
        start_time_sec: float = 25.0,
        end_time_sec: float = 45.0,
        heading_shift_deg: float = 120.0
    ) -> pd.DataFrame:
        """Injects impossible heading changes."""
        spoofed_df = df.copy()
        spoofed_df["scenario"] = "abnormal_heading"
        
        mask = (spoofed_df["timestamp"] >= start_time_sec) & (spoofed_df["timestamp"] <= end_time_sec)
        spoofed_df.loc[mask, "heading_deg"] = (spoofed_df.loc[mask, "heading_deg"] + heading_shift_deg) % 360.0
        spoofed_df.loc[mask, "is_spoofed"] = True
        
        return spoofed_df

    @staticmethod
    def inject_off_taxiway(
        df: pd.DataFrame,
        start_time_sec: float = 15.0,
        end_time_sec: float = 50.0,
        off_path_offset_deg: float = 0.005 # ~500 meters off taxiway into restricted field
    ) -> pd.DataFrame:
        """Pushes ground vehicle or aircraft off taxiway/runway paths."""
        spoofed_df = df.copy()
        spoofed_df["scenario"] = "off_taxiway"
        
        mask = (spoofed_df["timestamp"] >= start_time_sec) & (spoofed_df["timestamp"] <= end_time_sec)
        spoofed_df.loc[mask, "latitude"] = (spoofed_df.loc[mask, "latitude"] + off_path_offset_deg).round(6)
        spoofed_df.loc[mask, "is_spoofed"] = True
        
        return spoofed_df
