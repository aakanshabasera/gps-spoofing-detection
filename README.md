# GPS Spoofing Detection & Airport Navigation Integrity System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.25+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-12%20passed-brightgreen.svg)]()

A defensive cybersecurity system for detecting **GPS spoofing, trajectory manipulation, and navigation anomalies** in commercial aircraft and airport ground vehicles operating around Indira Gandhi International Airport (DEL / VIDP).

---

## Key Features

- **Multi-Layer Detection Engine**: Kinematic rules (speed, jump, drift, altitude, acceleration), geofence validation, and multi-source RADAR correlation.
- **Machine Learning Anomaly Model**: Unsupervised Isolation Forest model detecting complex spatial-temporal spoofing patterns.
- **Hybrid Risk Scoring**: Normalized 0–100 risk score and real-time SOC alert classification (`NORMAL`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **Interactive SOC Dashboard**:
  - **Spatial Trajectory**: Three.js WebGL 3D flight viewer loading 3D Airbus A320 & 3D Runway models.
  - **2D Operations Map**: Plotly Mapbox geospatial map displaying airport boundaries, runways, taxiways, and threat markers.
- **REST API & Database**: FastAPI endpoints (`/analyze`, `/alerts`) backed by SQLite persistence.

---

## Quick Start

### 1. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Streamlit SOC Dashboard
```bash
PYTHONPATH=. streamlit run dashboard/app.py
```
*Access dashboard at `http://localhost:8501`*

### 3. Run FastAPI REST API
```bash
PYTHONPATH=. uvicorn api.main:app --reload --port 8000
```
*Access API docs at `http://localhost:8000/docs`*

### 4. Run Test Suite
```bash
PYTHONPATH=. pytest tests/ -v
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
