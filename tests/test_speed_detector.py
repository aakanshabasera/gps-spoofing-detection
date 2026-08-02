import pytest
from simulator.aircraft_simulator import AircraftSimulator
from simulator.spoofing_scenarios import SpoofingScenarioGenerator
from detection.speed_detector import ImpossibleSpeedDetector


def test_speed_detector_normal_trajectory():
    sim = AircraftSimulator(asset_id="AI101", seed=42)
    normal_df = sim.generate_approach_trajectory(duration_sec=60, dt_sec=1.0)
    
    detector = ImpossibleSpeedDetector()
    alerts = detector.detect(normal_df)
    
    # Should be zero false positives on normal realistic flight trajectory
    assert len(alerts) == 0


def test_speed_detector_sudden_jump():
    sim = AircraftSimulator(asset_id="AI101", seed=42)
    normal_df = sim.generate_approach_trajectory(duration_sec=60, dt_sec=1.0)
    
    spoofed_df = SpoofingScenarioGenerator.inject_sudden_jump(
        normal_df, start_time_sec=20.0, end_time_sec=40.0
    )
    
    detector = ImpossibleSpeedDetector()
    alerts = detector.detect(spoofed_df)
    
    # Should catch the sudden position jump at t=20.0s (and return jump at t=41.0s)
    assert len(alerts) >= 1
    first_alert = alerts[0]
    assert first_alert["alert_type"] == "IMPOSSIBLE_SPEED"
    assert first_alert["severity"] == "CRITICAL"
    assert first_alert["asset_id"] == "AI101"
