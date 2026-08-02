import os
import streamlit as st
import pandas as pd
import yaml
from geospatial.airport_map import AirportMap
from simulator.aircraft_simulator import AircraftSimulator
from simulator.vehicle_simulator import GroundVehicleSimulator
from simulator.spoofing_scenarios import SpoofingScenarioGenerator
from detection.hybrid_engine import HybridRiskEngine
from ml.evaluate import ModelEvaluator
from dashboard.map import render_airport_map
from dashboard.three_map import render_3d_airport_model
from dashboard.alerts import render_alert_panel
from dashboard.analytics import render_analytics_panel

# Page Config
st.set_page_config(
    page_title="Airport Navigation Integrity & GPS Spoofing SOC",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Light Mode Corporate SOC Theme & Micro-Animations
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
    }
    
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        padding: 16px 20px !important;
        border-radius: 10px !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.05) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] *,
    [data-testid="stMetricLabel"] p,
    [data-testid="stMetricLabel"] label,
    [data-testid="stMetricLabel"] span {
        color: #1e293b !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        opacity: 1.0 !important;
    }

    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] *,
    [data-testid="stMetricValue"] div {
        color: #0f172a !important;
        font-weight: 800 !important;
        font-size: 28px !important;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px -2px rgba(0, 0, 0, 0.08);
    }
    
    .badge-normal {
        color: #059669;
        background-color: #ecfdf5;
        border: 1px solid #a7f3d0;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 14px;
        display: inline-block;
    }
    
    .badge-critical {
        color: #dc2626;
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 14px;
        display: inline-block;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.4); }
        70% { box-shadow: 0 0 0 8px rgba(220, 38, 38, 0); }
        100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 2px solid #e2e8f0;
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 6px 6px 0 0;
        font-weight: 500;
        color: #64748b;
    }

    .stTabs [aria-selected="true"] {
        color: #0f172a !important;
        border-bottom: 3px solid #2563eb !important;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# Load resources
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "thresholds.yaml")
GEOJSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "reference", "del_airport.geojson")

@st.cache_resource
def load_system_resources():
    airport_map = AirportMap(GEOJSON_PATH)
    hybrid_engine = HybridRiskEngine(airport_map, CONFIG_PATH)
    evaluator = ModelEvaluator(airport_map)
    return airport_map, hybrid_engine, evaluator

airport_map, hybrid_engine, evaluator = load_system_resources()

# Sidebar Controls
st.sidebar.title("Security Operations Center")
asset_type = st.sidebar.selectbox("Asset Category", ["aircraft", "ground_vehicle"])
scenario = st.sidebar.selectbox(
    "Simulation Scenario",
    ["Normal Movement", "Sudden Position Jump", "Gradual GPS Drift", "Wrong Altitude Spoof", "Off-Taxiway Violation"]
)

if asset_type == "aircraft":
    asset_id_input = st.sidebar.selectbox("Aircraft Flight / Tail ID", ["AI101", "BA204", "DL882", "EK501", "Custom ID..."])
    if asset_id_input == "Custom ID...":
        asset_id = st.sidebar.text_input("Enter Custom Aircraft ID", value="AI202").strip() or "AI202"
    else:
        asset_id = asset_id_input
else:
    asset_id_input = st.sidebar.selectbox("Ground Support Vehicle ID", ["TUG-04", "FUEL-02", "BAGGAGE-09", "Custom ID..."])
    if asset_id_input == "Custom ID...":
        asset_id = st.sidebar.text_input("Enter Custom Vehicle ID", value="TUG-08").strip() or "TUG-08"
    else:
        asset_id = asset_id_input

st.sidebar.markdown(f"**Active Monitored ID**: `{asset_id}`")

duration_sec = st.sidebar.slider("Simulation Duration (seconds)", min_value=30, max_value=180, value=90, step=15)

# Simulation Execution
@st.cache_data
def run_simulation_cached(asset_type, scenario, duration_sec, asset_id):
    if asset_type == "aircraft":
        sim = AircraftSimulator(asset_id=asset_id, seed=42)
        df = sim.generate_approach_trajectory(duration_sec=duration_sec)
    else:
        sim = GroundVehicleSimulator(asset_id=asset_id, seed=101)
        df = sim.generate_taxiway_route()

    if scenario == "Sudden Position Jump":
        df = SpoofingScenarioGenerator.inject_sudden_jump(df, start_time_sec=25.0, end_time_sec=55.0)
    elif scenario == "Gradual GPS Drift":
        df = SpoofingScenarioGenerator.inject_gradual_drift(df, start_time_sec=20.0, end_time_sec=70.0)
    elif scenario == "Wrong Altitude Spoof":
        df = SpoofingScenarioGenerator.inject_altitude_spoof(df, start_time_sec=20.0, end_time_sec=50.0)
    elif scenario == "Off-Taxiway Violation":
        df = SpoofingScenarioGenerator.inject_off_taxiway(df, start_time_sec=15.0, end_time_sec=45.0)
        
    return df

df = run_simulation_cached(asset_type, scenario, duration_sec, asset_id)

# Train ML baseline & compute hybrid risk scores
normal_df = run_simulation_cached(asset_type, "Normal Movement", duration_sec, asset_id)
hybrid_engine.train_ml_baseline(normal_df)
alerts = hybrid_engine.analyze_trajectory(df)
eval_metrics = evaluator.evaluate(df)

# Header Metrics
st.title("Airport Navigation Integrity & GPS Spoofing Detection Platform")
st.markdown("Defensive Cyber-Physical Security & Integrity Monitoring System")

m1, m2, m3, m4, m5 = st.columns(5)
crit_count = sum(1 for a in alerts if a["severity"] == "CRITICAL")
high_count = sum(1 for a in alerts if a["severity"] == "HIGH")

status_label = "CRITICAL ALERT" if crit_count > 0 else ("WARNING" if high_count > 0 else "NORMAL")
badge_class = "badge-critical" if crit_count > 0 or high_count > 0 else "badge-normal"

m1.markdown(f"**System Status**<br><span class='{badge_class}'>{status_label}</span>", unsafe_allow_html=True)
m2.metric("Monitored Assets", "1 Active")
m3.metric("Telemetry Points", len(df))
m4.metric("Active Alerts", len(alerts))
m5.metric("Critical Alerts", crit_count)

st.markdown("---")

# Main Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Spatial Operations & Trajectory",
    "Geospatial Operations Map",
    "Active Security Alerts",
    "Historical Analytics & Performance",
    "System Configuration & Scope"
])

with tab1:
    st.subheader(f"Spatial Navigation & Flight Operations — {scenario} ({asset_id})")
    render_3d_airport_model(df, alerts=alerts, height=580)

with tab2:
    st.subheader(f"2D Map Layer — {scenario} ({asset_id})")
    render_airport_map(airport_map.gdf, df=df, alerts=alerts)

with tab3:
    render_alert_panel(alerts, df=df)

with tab4:
    render_analytics_panel(df, alerts, eval_metrics)

with tab5:
    st.subheader("System Configuration & Defensive Scope")
    st.json(hybrid_engine.config)
    st.markdown("""
    **Defensive Scope Statement**
    This platform is strictly a defensive cybersecurity monitoring system designed for simulated or authorized telemetry analysis. It does not perform RF signal transmission, jamming, spoofing, or active manipulation of physical navigation systems.
    """)
