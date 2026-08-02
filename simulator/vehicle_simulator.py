import math
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from .noise_generator import GPSNoiseGenerator


class GroundVehicleSimulator:
    """
    Simulates movement of airport ground support vehicles (baggage tugs, fuel trucks, maintenance)
    following taxiway and apron service paths.
    """

    def __init__(self, asset_id: str = "TUG-04", asset_type: str = "ground_vehicle", seed: int = 101):
        self.asset_id = asset_id
        self.asset_type = asset_type
        self.noise_gen = GPSNoiseGenerator(lat_std_m=0.5, lon_std_m=0.5, alt_std_ft=0.5, seed=seed)

    def generate_taxiway_route(
        self,
        waypoints: List[Dict[str, float]] = None,
        speed_kts: float = 25.0,
        dt_sec: float = 1.0,
        add_noise: bool = True
    ) -> pd.DataFrame:
        """
        Generates a ground vehicle path moving between defined airport waypoints at a steady speed.
        """
        if waypoints is None:
            # Default Taxiway Alpha path at DEL airport
            waypoints = [
                {"lat": 28.5630, "lon": 77.0820},
                {"lat": 28.5480, "lon": 77.1200}
            ]
            
        records: List[Dict[str, Any]] = []
        timestamp = 0.0
        speed_ms = speed_kts * 0.514444
        
        for i in range(len(waypoints) - 1):
            p1 = waypoints[i]
            p2 = waypoints[i + 1]
            
            d_lat = p2["lat"] - p1["lat"]
            d_lon = p2["lon"] - p1["lon"]
            heading_deg = (math.degrees(math.atan2(d_lon, d_lat)) + 360) % 360
            
            dist_lat_m = d_lat * 111_000.0
            dist_lon_m = d_lon * 97_000.0
            segment_dist_m = math.sqrt(dist_lat_m**2 + dist_lon_m**2)
            
            num_steps = int(segment_dist_m / (speed_ms * dt_sec))
            if num_steps <= 0:
                continue
                
            step_lat = d_lat / num_steps
            step_lon = d_lon / num_steps
            
            curr_lat = p1["lat"]
            curr_lon = p1["lon"]
            
            for _ in range(num_steps):
                if add_noise:
                    rep_lat, rep_lon, rep_alt = self.noise_gen.apply_noise(curr_lat, curr_lon, 0.0)
                else:
                    rep_lat, rep_lon, rep_alt = round(curr_lat, 6), round(curr_lon, 6), 0.0
                    
                records.append({
                    "asset_id": self.asset_id,
                    "asset_type": self.asset_type,
                    "timestamp": timestamp,
                    "latitude": rep_lat,
                    "longitude": rep_lon,
                    "altitude_ft": rep_alt,
                    "speed_kts": round(speed_kts, 2),
                    "heading_deg": round(heading_deg, 1),
                    "acceleration_ms2": 0.0,
                    "data_source": "GROUND_GPS",
                    "scenario": "normal_taxiway",
                    "is_spoofed": False
                })
                
                timestamp += dt_sec
                curr_lat += step_lat
                curr_lon += step_lon
                
        return pd.DataFrame(records)
