import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import pandas as pd
from geospatial.airport_map import AirportMap
from detection.hybrid_engine import HybridRiskEngine
from database import init_db, save_readings, save_alerts, get_all_alerts
from simulator.aircraft_simulator import AircraftSimulator
from simulator.vehicle_simulator import GroundVehicleSimulator
from simulator.spoofing_scenarios import SpoofingScenarioGenerator

app = FastAPI(
    title="Airport Navigation Integrity Monitoring API",
    description="Defensive Cybersecurity REST API for GPS Spoofing Detection and Airport Integrity Monitoring",
    version="1.0.0"
)

# Initialize airport reference layer and hybrid detection engine
geojson_path = os.path.join(os.path.dirname(__file__), "..", "data", "reference", "del_airport.geojson")
airport_map = AirportMap(geojson_path)
hybrid_engine = HybridRiskEngine(airport_map)
init_db()


class SimulationRequest(BaseModel):
    asset_id: str = "AI101"
    asset_type: str = "aircraft" # aircraft / ground_vehicle
    scenario: str = "normal" # normal, sudden_jump, gradual_drift, wrong_altitude, off_taxiway
    duration_sec: int = 60


class TelemetryItem(BaseModel):
    asset_id: str
    asset_type: str = "aircraft"
    timestamp: float
    latitude: float
    longitude: float
    altitude_ft: float = 0.0
    speed_kts: float = 0.0
    heading_deg: float = 0.0
    acceleration_ms2: float = 0.0
    data_source: str = "GPS_ADSB"


@app.get("/")
def read_root():
    return {
        "status": "OPERATIONAL",
        "system": "GPS Spoofing Detection & Airport Navigation Integrity Monitoring System",
        "airport": "Indira Gandhi International Airport (DEL / VIDP)",
        "version": "1.0.0"
    }


@app.get("/airport")
def get_airport_infrastructure():
    """Returns the GeoJSON airport reference layer."""
    return airport_map.gdf.__geo_interface__


@app.get("/alerts")
def get_alerts(min_severity: Optional[str] = None):
    """Retrieves all detected security alerts."""
    all_alerts = get_all_alerts()
    if min_severity:
        all_alerts = [a for a in all_alerts if a["severity"].upper() == min_severity.upper()]
    return {"count": len(all_alerts), "alerts": all_alerts}


@app.post("/simulate")
def run_simulation(req: SimulationRequest):
    """Triggers dynamic movement trajectory simulation and analyzes for spoofing."""
    if req.asset_type == "aircraft":
        sim = AircraftSimulator(asset_id=req.asset_id, seed=42)
        df = sim.generate_approach_trajectory(duration_sec=req.duration_sec)
    else:
        sim = GroundVehicleSimulator(asset_id=req.asset_id, seed=101)
        df = sim.generate_taxiway_route()

    # Apply requested spoofing scenario
    if req.scenario == "sudden_jump":
        df = SpoofingScenarioGenerator.inject_sudden_jump(df, start_time_sec=20.0, end_time_sec=40.0)
    elif req.scenario == "gradual_drift":
        df = SpoofingScenarioGenerator.inject_gradual_drift(df, start_time_sec=20.0, end_time_sec=50.0)
    elif req.scenario == "wrong_altitude":
        df = SpoofingScenarioGenerator.inject_altitude_spoof(df, start_time_sec=20.0, end_time_sec=40.0)
    elif req.scenario == "off_taxiway":
        df = SpoofingScenarioGenerator.inject_off_taxiway(df, start_time_sec=15.0, end_time_sec=35.0)

    # Save telemetry and run hybrid detection
    save_readings(df)
    alerts = hybrid_engine.analyze_trajectory(df)
    save_alerts(alerts)

    return {
        "asset_id": req.asset_id,
        "scenario": req.scenario,
        "telemetry_points": len(df),
        "alerts_generated": len(alerts),
        "alerts": alerts
    }


@app.post("/analyze")
def analyze_telemetry(items: List[TelemetryItem]):
    """Analyzes user-submitted telemetry points for GPS spoofing anomalies."""
    if not items:
        raise HTTPException(status_code=400, detail="Empty telemetry batch.")

    df = pd.DataFrame([item.model_dump() for item in items])
    alerts = hybrid_engine.analyze_trajectory(df)
    save_alerts(alerts)
    return {"telemetry_count": len(df), "alerts_detected": len(alerts), "alerts": alerts}


@app.get("/statistics")
def get_statistics():
    """Returns high-level detection performance and alert counts."""
    all_alerts = get_all_alerts()
    severity_counts = {}
    type_counts = {}
    for a in all_alerts:
        s = a["severity"]
        t = a["alert_type"]
        severity_counts[s] = severity_counts.get(s, 0) + 1
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "total_alerts": len(all_alerts),
        "alerts_by_severity": severity_counts,
        "alerts_by_type": type_counts
    }
