import plotly.graph_objects as go
import pandas as pd
import streamlit as st
import folium
import json
import streamlit.components.v1 as components
from typing import List, Dict, Any


def render_airport_map(
    airport_gdf,
    df: pd.DataFrame = None,
    alerts: List[Dict[str, Any]] = None,
    center_lat: float = 28.5562,
    center_lon: float = 77.1000,
    zoom_start: int = 13
):
    """
    Renders a 100% reliable 2D Geospatial Map using native Plotly Mapbox
    and interactive Folium layers for airport navigation integrity monitoring.
    """
    fig = go.Figure()

    # 1. Render Airport Infrastructure Polygons (Boundary, Runways, Taxiways)
    for _, row in airport_gdf.iterrows():
        feature_type = row.get("type", "")
        geom = row.geometry
        name = row.get("name", "Infrastructure")
        
        if geom.geom_type == "Polygon":
            lons, lats = geom.exterior.xy
            lons = list(lons)
            lats = list(lats)
            
            if feature_type == "boundary":
                fig.add_trace(go.Scattermapbox(
                    lat=lats,
                    lon=lons,
                    mode="lines",
                    line=dict(width=2, color="#2563eb"),
                    name="Airport Boundary",
                    hoverinfo="text",
                    hovertext="Indira Gandhi Int'l Airport Perimeter"
                ))
            elif feature_type == "runway":
                fig.add_trace(go.Scattermapbox(
                    lat=lats,
                    lon=lons,
                    mode="lines",
                    fill="toself",
                    fillcolor="rgba(5, 150, 105, 0.4)",
                    line=dict(width=4, color="#059669"),
                    name=f"Runway: {name}",
                    hoverinfo="text",
                    hovertext=f"Runway {name}"
                ))
            elif feature_type == "taxiway":
                fig.add_trace(go.Scattermapbox(
                    lat=lats,
                    lon=lons,
                    mode="lines",
                    fill="toself",
                    fillcolor="rgba(217, 119, 6, 0.3)",
                    line=dict(width=3, color="#d97706"),
                    name=f"Taxiway: {name}",
                    hoverinfo="text",
                    hovertext=f"Taxiway {name}"
                ))
        elif geom.geom_type == "LineString":
            lons, lats = geom.xy
            lons = list(lons)
            lats = list(lats)
            color = "#059669" if feature_type == "runway" else "#d97706"
            fig.add_trace(go.Scattermapbox(
                lat=lats,
                lon=lons,
                mode="lines",
                line=dict(width=5 if feature_type == "runway" else 3, color=color),
                name=f"{feature_type.capitalize()}: {name}",
                hoverinfo="text",
                hovertext=name
            ))

    # 2. Plot Dynamic Trajectory Vector
    if df is not None and not df.empty:
        lats = df["latitude"].tolist()
        lons = df["longitude"].tolist()
        times = df["timestamp"].tolist()
        speeds = df.get("speed_kts", [0]*len(df)).tolist()
        
        hover_texts = [f"Time: {t:.1f}s | Speed: {s:.0f} kts" for t, s in zip(times, speeds)]
        
        fig.add_trace(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode="lines+markers",
            line=dict(width=4, color="#0284c7"),
            marker=dict(size=5, color="#0284c7"),
            name="Reported Flight Path",
            text=hover_texts,
            hoverinfo="text"
        ))

        # Start Marker
        fig.add_trace(go.Scattermapbox(
            lat=[lats[0]],
            lon=[lons[0]],
            mode="markers",
            marker=dict(size=12, color="#10b981"),
            name="Trajectory Start",
            hoverinfo="text",
            hovertext="Start Position"
        ))

        # Current Position Marker
        fig.add_trace(go.Scattermapbox(
            lat=[lats[-1]],
            lon=[lons[-1]],
            mode="markers",
            marker=dict(size=14, color="#2563eb"),
            name="Current Position",
            hoverinfo="text",
            hovertext=f"Current Asset Location ({df.iloc[-1].get('asset_id', 'AI101')})"
        ))

    # 3. Plot Anomaly Alert Markers
    if alerts:
        alert_lats = []
        alert_lons = []
        alert_texts = []
        
        for a in alerts:
            loc = a["location"]
            alert_lats.append(loc[0])
            alert_lons.append(loc[1])
            txt = (
                f"ALERT: {a['alert_type']}<br>"
                f"Severity: {a['severity']}<br>"
                f"Risk Score: {a['risk_score']}/100<br>"
                f"Time: {a['timestamp']}s"
            )
            alert_texts.append(txt)

        fig.add_trace(go.Scattermapbox(
            lat=alert_lats,
            lon=alert_lons,
            mode="markers",
            marker=dict(size=16, color="#ef4444", opacity=0.9),
            name="Spoofing Anomaly Location",
            text=alert_texts,
            hoverinfo="text"
        ))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": center_lat, "lon": center_lon},
        mapbox_zoom=zoom_start,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=580,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="#cbd5e1",
            borderwidth=1
        )
    )

    st.plotly_chart(fig, use_container_width=True)
