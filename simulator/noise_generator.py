import numpy as np
from typing import Tuple


class GPSNoiseGenerator:
    """
    Simulates realistic GPS measurement noise including Gaussian position jitter,
    altitude variance, and temporary reading dropouts.
    """

    def __init__(self, lat_std_m: float = 2.0, lon_std_m: float = 2.0, alt_std_ft: float = 5.0, seed: int = 42):
        self.lat_std_deg = lat_std_m / 111_000.0  # Approx 111 km per degree
        self.lon_std_deg = lon_std_m / 97_000.0   # Approx 97 km per degree at 28°N
        self.alt_std_ft = alt_std_ft
        self.rng = np.random.default_rng(seed)

    def apply_noise(self, lat: float, lon: float, alt_ft: float) -> Tuple[float, float, float]:
        """Adds zero-mean Gaussian noise to position coordinates."""
        noisy_lat = lat + self.rng.normal(0, self.lat_std_deg)
        noisy_lon = lon + self.rng.normal(0, self.lon_std_deg)
        noisy_alt = max(0.0, alt_ft + self.rng.normal(0, self.alt_std_ft))
        return round(noisy_lat, 6), round(noisy_lon, 6), round(noisy_alt, 2)
