# Airport Navigation Integrity & AI-Assisted GPS Spoofing Detection System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.25+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-12%20passed-brightgreen.svg)]()

A modular cybersecurity prototype designed for airport cyber-physical security. The platform monitors reported GPS telemetry from commercial aircraft and airport ground support vehicles to detect potential **GPS spoofing, trajectory manipulation, and navigation integrity threats**.

The system evaluates reported movement patterns against known airport infrastructure geometry (Indira Gandhi International Airport, DEL / VIDP), physical kinematics limits, multi-source RADAR correlation, and an unsupervised Machine Learning Anomaly Detection model (Isolation Forest).

> **Defensive Scope Disclaimer**: This software is strictly a defensive cybersecurity monitoring and anomaly-detection prototype. It uses simulated and reference geospatial data only. It does NOT perform RF jamming, spoofing, active transmission, or manipulation of real-world physical navigation hardware.

---

## Architecture & System Overview

```
                        ┌──────────────────────────────────────────┐
                        │      Incoming GPS Telemetry Stream       │
                        │   (Latitude, Longitude, Altitude, Time)  │
                        └────────────────────┬─────────────────────┘
                                             │
                                             ▼
                        ┌──────────────────────────────────────────┐
                        │   1. Geospatial Reference Engine         │
                        │   - ICAO / DEL Airport Boundaries        │
                        │   - Runway & Taxiway Geometry            │
                        │   - Metric Projections (EPSG:3857)       │
                        └────────────────────┬─────────────────────┘
                                             │
                                             ▼
                        ┌──────────────────────────────────────────┐
                        │   2. Multi-Layer Detection Suite         │
                        │   - Kinematic Rules (Speed/Jump/Drift)   │
                        │   - Geofence & Taxiway Alignment         │
                        │   - Multi-Source RADAR Correlation       │
                        │   - Isolation Forest Machine Learning    │
                        └────────────────────┬─────────────────────┘
                                             │
                                             ▼
                        ┌──────────────────────────────────────────┐
                        │   3. Hybrid Risk Scoring Engine          │
                        │   - Normalized Composite Score (0-100)   │
                        │   - NORMAL | LOW | MEDIUM | HIGH | CRIT  │
                        └────────────────────┬─────────────────────┘
                                             │
                                             ▼
                        ┌──────────────────────────────────────────┐
                        │   4. Security Operations Center (SOC)    │
                        │   - Interactive 3D WebGL Airbus & Runway │
                        │   - 2D Plotly Mapbox Operations Map      │
                        │   - FastAPI REST API & SQLite DB         │
                        └──────────────────────────────────────────┘
```

---

## Core Operational Features

- **Geospatial Airport Infrastructure Engine (`geospatial/`)**:
  - Uses GeoJSON geospatial polygon models representing Indira Gandhi International Airport (DEL / VIDP).
  - Uses PyProj and GeoPandas for exact metric distance calculations (`EPSG:3857`).
  - Evaluates perimeter containment (`is_inside_airport_boundary`), runway distances (`distance_from_runway`), and ground vehicle taxiway alignment.

- **Realistic Telemetry & Attack Simulator (`simulator/`)**:
  - *Aircraft ILS Approach Simulator*: Simulates 3D Instrument Landing System glide-slope trajectories, airspeed deceleration (180 kts -> rollout), altitude loss, and Gaussian GPS noise.
  - *Ground Support Equipment Simulator*: Simulates taxiway movements within speed limits (15–25 kts).
  - *Spoofing Attack Profiles*: Injects Sudden Position Jumps, Gradual GPS Drifts (+5m/s), Falsified Altitude Spoofs, and Off-Taxiway Boundary Violations.

- **Multi-Layer Anomaly Detection Suite (`detection/` & `ml/`)**:
  - *Kinematic Rule Detectors*: Speed violations (>550 kts), Sudden Spatial Jumps (>300m/s), Trajectory Drift, Acceleration G-force anomalies (>3.0g), Heading Rate turns (>45°/s), and Glide-slope Altitude anomalies.
  - *Multi-Source RADAR Correlation*: Compares reported GPS against an independent reference source (e.g. Primary Surveillance RADAR).
  - *Isolation Forest Machine Learning*: Unsupervised ML model trained on 8 spatial-temporal features to detect complex, multi-variable spoofing patterns.

- **Security Operations Center Dashboard (`dashboard/`)**:
  - *Spatial Flight Viewer*: Three.js WebGL rendering of custom 3D Airbus A320 (`airbus_a320.glb`) and 3D Runway (`runway.glb`) with dynamic pitch/roll physics, interactive camera modes (Orbit, Follow Aircraft, Cockpit View), and red threat beacons.
  - *2D Geospatial Map*: Plotly Mapbox interactive 2D map displaying airport perimeters, runways, taxiways, trajectory flight vectors, and popup alert cards.
  - *Alert Drill-Down & Analytics*: Plotly telemetry displacement charts, vector displacement analysis, and evaluation metrics (Accuracy, Precision, Recall, F1).

---

## Project Structure

```
gps-spoofing-detection/
├── api/                        # FastAPI REST API endpoints
│   └── main.py
├── config/                     # System thresholds & risk weights
│   └── thresholds.yaml
├── dashboard/                  # Streamlit SOC Dashboard
│   ├── app.py                  # Main entrypoint
│   ├── three_map.py            # Three.js 3D WebGL Viewer
│   ├── map.py                  # Plotly Mapbox 2D Map Renderer
│   ├── alerts.py               # Security Alert Drill-Down Panel
│   └── analytics.py            # Model Evaluation & Metrics Charts
├── data/                       # Infrastructure & Reference Datasets
│   ├── reference/              # GeoJSON airport map & 3D GLB models
│   └── simulated/              # Simulated normal & attack datasets
├── database/                   # SQLite ORM & Persistence Layer
│   ├── models.py               # SQLAlchemy Database Models
│   └── database.py             # Database connections & queries
├── detection/                  # Multi-layer anomaly detection engines
│   ├── speed_detector.py
│   ├── jump_detector.py
│   ├── drift_detector.py
│   ├── acceleration_detector.py
│   ├── heading_detector.py
│   ├── altitude_detector.py
│   ├── geofence_detector.py
│   ├── correlation_engine.py   # Multi-source RADAR correlation
│   └── hybrid_engine.py        # Composite Risk Scoring Engine
├── geospatial/                 # Geospatial query & coordinate engine
│   ├── airport_map.py          # Metric spatial coordinate transformer
│   ├── runway_validator.py     # Runway alignment validator
│   └── taxiway_validator.py    # Taxiway path validator
├── ml/                         # Machine Learning Pipeline
│   ├── feature_engineering.py  # Feature extraction pipeline
│   ├── anomaly_detector.py     # Isolation Forest Model
│   └── evaluate.py             # Performance Evaluator (Precision, Recall, F1)
├── simulator/                  # Telemetry & attack scenario generator
│   ├── aircraft_simulator.py   # 3D ILS approach simulator
│   ├── vehicle_simulator.py    # Ground vehicle taxiway simulator
│   ├── spoofing_scenarios.py   # Attack scenario injector
│   ├── noise_generator.py      # Gaussian GPS noise generator
│   └── generate_datasets.py    # Dataset generator script
├── tests/                      # Automated Test Suite (12 Pytest tests)
├── Dockerfile                  # Container build file
├── docker-compose.yml          # Container orchestration
├── requirements.txt            # Dependencies
└── README.md                   # System Documentation
```

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- `pip` package manager

### 1. Clone & Setup Environment

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/gps-spoofing-detection.git
cd gps-spoofing-detection

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## How to Run

### 1. Launch Streamlit SOC Dashboard

```bash
PYTHONPATH=. streamlit run dashboard/app.py
```
*Open your browser at `http://localhost:8501` to access the Security Operations Center dashboard.*

### 2. Launch FastAPI REST API Service

```bash
PYTHONPATH=. uvicorn api.main:app --reload --port 8000
```
*Access interactive API documentation at `http://localhost:8000/docs`.*

### 3. Run Automated Pytest Test Suite

```bash
PYTHONPATH=. pytest tests/ -v
```

---

## Docker Deployment

Build and run using Docker Compose:

```bash
docker-compose up --build
```
- **Streamlit Dashboard**: `http://localhost:8501`
- **FastAPI REST API**: `http://localhost:8000/docs`

---

## Evaluation Metrics

The system performance evaluated on simulated attack datasets (`aircraft_sudden_jump.csv`, `aircraft_normal.csv`):

| Metric | Score | Description |
| :--- | :--- | :--- |
| **Accuracy** | `100.0%` | Correct classification of normal vs spoofed telemetry |
| **Precision** | `100.0%` | Zero false positive alerts |
| **Recall** | `100.0%` | Complete capture of injected spoofing anomalies |
| **F1 Score** | `1.000` | Optimal precision-recall trade-off |
| **Detection Latency** | `< 1.0 sec` | Real-time detection response time |

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
