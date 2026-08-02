import os
import pytest
from fastapi.testclient import TestClient
from geospatial.airport_map import AirportMap
from simulator.aircraft_simulator import AircraftSimulator
from simulator.vehicle_simulator import GroundVehicleSimulator
from simulator.spoofing_scenarios import SpoofingScenarioGenerator
from detection.hybrid_engine import HybridRiskEngine
from ml.evaluate import ModelEvaluator
from database import init_db, save_readings, get_all_alerts
from api.main import app


@pytest.fixture
def system_components():
    geojson_path = os.path.join(os.path.dirname(__file__), "..", "data", "reference", "del_airport.geojson")
    airport_map = AirportMap(geojson_path)
    engine = HybridRiskEngine(airport_map)
    evaluator = ModelEvaluator(airport_map)
    return airport_map, engine, evaluator


def test_ground_vehicle_simulation(system_components):
    _, engine, _ = system_components
    vehicle_sim = GroundVehicleSimulator(asset_id="TUG-04", seed=101)
    df = vehicle_sim.generate_taxiway_route()
    
    assert len(df) > 0
    assert (df["asset_type"] == "ground_vehicle").all()
    
    alerts = engine.analyze_trajectory(df)
    # Zero false positives on normal taxiway route
    assert len(alerts) == 0


def test_altitude_spoof_detection(system_components):
    _, engine, _ = system_components
    vehicle_sim = GroundVehicleSimulator(asset_id="TUG-04", seed=101)
    df = vehicle_sim.generate_taxiway_route()
    
    spoofed_df = SpoofingScenarioGenerator.inject_altitude_spoof(df, start_time_sec=5.0, end_time_sec=15.0)
    alerts = engine.analyze_trajectory(spoofed_df)
    
    assert len(alerts) > 0
    alt_alerts = [a for a in alerts if a["alert_type"] == "WRONG_ALTITUDE"]
    assert len(alt_alerts) > 0
    assert alt_alerts[0]["severity"] == "CRITICAL"


def test_gradual_drift_detection(system_components):
    _, engine, _ = system_components
    sim = AircraftSimulator(asset_id="AI101", seed=42)
    df = sim.generate_approach_trajectory(duration_sec=60)
    
    spoofed_df = SpoofingScenarioGenerator.inject_gradual_drift(df, start_time_sec=20.0, end_time_sec=50.0)
    alerts = engine.analyze_trajectory(spoofed_df)
    
    assert len(alerts) > 0


def test_database_persistence():
    init_db()
    sim = AircraftSimulator(asset_id="AI999", seed=99)
    df = sim.generate_approach_trajectory(duration_sec=10)
    save_readings(df)
    # Verify no error raised
    assert True


def test_fastapi_endpoints():
    client = TestClient(app)
    
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "OPERATIONAL"
    
    res_airport = client.get("/airport")
    assert res_airport.status_code == 200
    
    res_stats = client.get("/statistics")
    assert res_stats.status_code == 200
