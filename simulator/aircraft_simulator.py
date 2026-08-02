import math
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from .noise_generator import GPSNoiseGenerator


class AircraftSimulator:
    """
    Simulates physically realistic aircraft kinematics during approach, touchdown, and rollout.
    """

    def __init__(self, asset_id: str = "AI101", asset_type: str = "aircraft", seed: int = 42):
        self.asset_id = asset_id
        self.asset_type = asset_type
        self.noise_gen = GPSNoiseGenerator(seed=seed)

    def generate_approach_trajectory(
        self,
        start_lat: float = 28.5750,
        start_lon: float = 77.0400,
        start_alt_ft: float = 1500.0,
        end_lat: float = 28.5500,
        end_lon: float = 77.1220,
        duration_sec: int = 120,
        dt_sec: float = 1.0,
        add_noise: bool = True
    ) -> pd.DataFrame:
        """
        Generates a 3D approach flight path ending in runway touchdown and deceleration.
        """
        records: List[Dict[str, Any]] = []
        num_steps = int(duration_sec / dt_sec)
        
        # Calculate track bearing (heading)
        d_lat = end_lat - start_lat
        d_lon = end_lon - start_lon
        heading_deg = (math.degrees(math.atan2(d_lon, d_lat)) + 360) % 360
        
        # Calculate total ground distance in meters
        dist_lat_m = d_lat * 111_000.0
        dist_lon_m = d_lon * 97_000.0
        total_dist_m = math.sqrt(dist_lat_m**2 + dist_lon_m**2)
        
        # Speed profile: approach at 140 kts (72 m/s), decelerating post touchdown
        approach_speed_kts = 140.0
        approach_speed_ms = approach_speed_kts * 0.514444
        
        # Unit direction vector along heading
        rad_heading = math.radians(heading_deg)
        dir_lat = math.cos(rad_heading)
        dir_lon = math.sin(rad_heading)

        current_lat = start_lat
        current_lon = start_lon
        current_alt_ft = start_alt_ft
        current_speed_kts = approach_speed_kts

        for step in range(num_steps):
            timestamp_sec = float(step * dt_sec)
            
            # Kinematics state calculation
            if step < int(num_steps * 0.75):
                # Airborne approach phase
                current_alt_ft = max(0.0, start_alt_ft - step * (start_alt_ft / (num_steps * 0.75)))
                current_speed_kts = approach_speed_kts
                acceleration_ms2 = 0.0
            else:
                # Touchdown & Rollout braking phase
                current_alt_ft = 0.0
                current_speed_kts = max(20.0, current_speed_kts - 2.5 * dt_sec) # Decelerate
                acceleration_ms2 = -2.5 * 0.514444

            # Update coordinates based on instantaneous speed in m/s
            speed_ms = current_speed_kts * 0.514444
            step_dist_m = speed_ms * dt_sec
            
            current_lat += (step_dist_m * dir_lat) / 111_000.0
            current_lon += (step_dist_m * dir_lon) / 97_000.0

            if add_noise:
                rep_lat, rep_lon, rep_alt = self.noise_gen.apply_noise(current_lat, current_lon, current_alt_ft)
            else:
                rep_lat, rep_lon, rep_alt = round(current_lat, 6), round(current_lon, 6), round(current_alt_ft, 2)

            records.append({
                "asset_id": self.asset_id,
                "asset_type": self.asset_type,
                "timestamp": timestamp_sec,
                "latitude": rep_lat,
                "longitude": rep_lon,
                "altitude_ft": rep_alt,
                "speed_kts": round(current_speed_kts, 2),
                "heading_deg": round(heading_deg, 1),
                "acceleration_ms2": round(acceleration_ms2, 2),
                "data_source": "GPS_ADSB",
                "scenario": "normal_approach",
                "is_spoofed": False
            })

        return pd.DataFrame(records)
