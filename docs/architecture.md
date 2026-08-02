# AI-Assisted GPS Spoofing Detection & Airport Navigation Integrity Monitoring System
## Technical Architecture & System Specification

### 1. System Overview & Problem Statement
Global Positioning System (GPS) vulnerabilities expose aircraft and airport ground support equipment to cyber-physical security risks. GPS spoofing involves injecting falsified satellite signals, causing receiver positions to drift, jump, or report physically impossible trajectories. 

This platform acts as an **independent defensive integrity monitoring engine** that cross-validates dynamic broadcast movement data (such as ADS-B or ground telemetry) against airport geospatial infrastructure (ICAO boundaries, runways, taxiways) and independent reference sources.

---

### 2. Logical Data Pipeline Architecture

```
                       +-----------------------------------+
                       | Simulated Dynamic Movement Data   |
                       | (Aircraft / Ground Vehicles)     |
                       +-----------------+-----------------+
                                         |
                                         v
                       +-----------------+-----------------+
                       | Ingestion & Schema Validation    |
                       +-----------------+-----------------+
                                         |
                                         v
                       +-----------------+-----------------+
                       | Feature Engineering Pipeline      |
                       | (Speed, Acceleration, Heading    |
                       |  Change, Distance to Runway)     |
                       +-----------------+-----------------+
                                         |
                                         v
            +----------------------------+----------------------------+
            |                                                         |
            v                                                         v
+-----------+-------------------+                         +-----------+-------------------+
| Rule-Based Detection Engine   |                         | Geospatial Reference Engine   |
| - Impossible Speed            |                         | - Airport Boundary Check  |
| - Position Jump               |                         | - Runway/Taxiway Deviation|
| - Gradual Drift               |                         | - Runway Heading Alignment|
| - Implausible Acceleration    |                         +-----------+-------------------+
| - Heading & Altitude Anomaly  |                                     |
+-----------+-------------------+                                     |
            |                                                         |
            +----------------------------+----------------------------+
                                         |
                                         v
                       +-----------------+-----------------+
                       | Multi-Source Correlation Engine   |
                       | (GPS vs. Independent Reference)  |
                       +-----------------+-----------------+
                                         |
                                         v
                       +-----------------+-----------------+
                       | ML Anomaly Scoring Engine         |
                       | (Isolation Forest)               |
                       +-----------------+-----------------+
                                         |
                                         v
                       +-----------------+-----------------+
                       | Hybrid Risk Scoring Engine       |
                       | (Configurable Weights & Rules)   |
                       +-----------------+-----------------+
                                         |
                                         v
                       +-----------------+-----------------+
                       | Alert Generator & SOC Dashboard  |
                       | (Streamlit & SQLite Database)    |
                       +-----------------------------------+
```

---

### 3. Data Schemas

#### A. Dynamic Movement Schema (`data/simulated/*.csv`)
| Field Name | Type | Description | Example |
|------------|------|-------------|---------|
| `asset_id` | string | Unique aircraft or vehicle tail/registration ID | `AI101` |
| `asset_type` | string | `aircraft` or `ground_vehicle` | `aircraft` |
| `timestamp` | ISO-8601 / float | Timestamp of observation | `2026-07-29T18:00:00Z` |
| `latitude` | float | Reported GPS latitude in decimal degrees | `28.5562` |
| `longitude` | float | Reported GPS longitude in decimal degrees | `77.1000` |
| `altitude_ft` | float | Altitude above MSL in feet | `150.0` |
| `speed_kts` | float | Ground speed in knots | `135.0` |
| `heading_deg` | float | True heading in degrees (0–359.9°) | `270.5` |
| `acceleration_ms2` | float | Instantaneous acceleration in m/s² | `0.45` |
| `data_source` | string | Primary position receiver (`GPS_ADSB`, `GROUND_GPS`) | `GPS_ADSB` |
| `scenario` | string | Scenario name (e.g. `normal_approach`, `sudden_jump`) | `sudden_jump` |
| `is_spoofed` | boolean | Ground-truth flag (**used ONLY for evaluation**) | `True` |

#### B. Alert Schema
| Field Name | Type | Description |
|------------|------|-------------|
| `alert_id` | string | UUID identifier for the alert |
| `timestamp` | string | Time alert was raised |
| `asset_id` | string | Affected asset ID |
| `asset_type` | string | Type of asset (`aircraft`, `vehicle`) |
| `alert_type` | string | Primary violation category (`IMPOSSIBLE_SPEED`, `POSITION_JUMP`, etc.) |
| `severity` | string | `NORMAL`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `risk_score` | float | Computed cumulative risk score (0–100) |
| `confidence` | float | Confidence metric (0.0 to 1.0) |
| `location` | tuple | (latitude, longitude) of anomaly |
| `detected_indicators` | list | List of triggered rule descriptions |
| `expected_position` | tuple | Estimated physical position (lat, lon) |
| `reported_position` | tuple | Reported GPS position (lat, lon) |
| `explanation` | string | Human-readable alert summary for SOC analysts |
| `status` | string | Alert status (`NEW`, `ACKNOWLEDGED`, `RESOLVED`, `FALSE_POSITIVE`) |

---

### 4. Detection Physics & Mathematical Formulation

#### Impossible Speed Calculation (Geodesic / Haversine)
Given consecutive GPS readings $P_1 = (\text{lat}_1, \text{lon}_1, t_1)$ and $P_2 = (\text{lat}_2, \text{lon}_2, t_2)$:
1. Calculate Vincenty/Haversine distance $\Delta d = \text{GeodesicDistance}(P_1, P_2)$ in meters.
2. Time interval $\Delta t = t_2 - t_1$ in seconds.
3. Computed Speed $v = \frac{\Delta d}{\Delta t}$.
4. If $v > v_{\text{max\_allowed\_for\_asset\_state}}$, flag `IMPOSSIBLE_SPEED`.

---

### 5. Defensive Scope & Safety Statement
This system is strictly a **defensive monitoring framework**. It operates purely on passive telemetry analysis and simulation data. It contains no capabilities to transmit radio-frequency signals, generate jamming signals, or tamper with operational navigation avionics.
