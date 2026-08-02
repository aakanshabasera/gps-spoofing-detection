import pytest
import pandas as pd
from simulator.aircraft_simulator import AircraftSimulator
from simulator.spoofing_scenarios import SpoofingScenarioGenerator


def test_generate_approach_trajectory():
    sim = AircraftSimulator(asset_id="AI101", seed=42)
    df = sim.generate_approach_trajectory(duration_sec=60, dt_sec=1.0)
    
    assert len(df) == 60
    assert "latitude" in df.columns
    assert "longitude" in df.columns
    assert "speed_kts" in df.columns
    assert "is_spoofed" in df.columns
    assert (df["is_spoofed"] == False).all()


def test_inject_sudden_jump():
    sim = AircraftSimulator(asset_id="AI101", seed=42)
    normal_df = sim.generate_approach_trajectory(duration_sec=60, dt_sec=1.0)
    
    spoofed_df = SpoofingScenarioGenerator.inject_sudden_jump(
        normal_df, start_time_sec=20.0, end_time_sec=40.0
    )
    
    assert len(spoofed_df) == 60
    spoofed_rows = spoofed_df[spoofed_df["is_spoofed"] == True]
    assert len(spoofed_rows) == 21 # timestamps 20 through 40 inclusive
    assert (spoofed_df.loc[spoofed_df["timestamp"] == 25, "scenario"] == "sudden_position_jump").all()
