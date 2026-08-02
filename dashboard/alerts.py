import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict, Any


def render_alert_panel(alerts: List[Dict[str, Any]], df: pd.DataFrame = None):
    """
    Renders the security incident alert panel and interactive drill-down view
    using a clean, professional corporate UI.
    """
    st.subheader("Active Security Alerts & Incident Analysis")
    
    if not alerts:
        st.info("System Status Normal — No active GPS spoofing anomalies detected.")
        return

    # Convert alerts to DataFrame for display
    alert_rows = []
    for a in alerts:
        alert_rows.append({
            "Alert ID": a["alert_id"][:8],
            "Timestamp (s)": a["timestamp"],
            "Asset": a["asset_id"],
            "Type": a["asset_type"],
            "Alert Category": a["alert_type"],
            "Severity": a["severity"],
            "Risk Score": f"{a['risk_score']:.0f}/100",
            "Confidence": f"{a['confidence']*100:.0f}%",
            "Status": a["status"]
        })
        
    alerts_df = pd.DataFrame(alert_rows)
    st.dataframe(alerts_df, use_container_width=True)

    # Drill-down selector
    selected_idx = st.selectbox(
        "Select Alert for Detailed Analysis:",
        range(len(alerts)),
        format_func=lambda i: f"[{alerts[i]['severity']}] {alerts[i]['alert_type']} - Asset {alerts[i]['asset_id']} @ t={alerts[i]['timestamp']}s"
    )

    if selected_idx is not None:
        sel_alert = alerts[selected_idx]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### Incident Details")
            st.markdown(f"**Asset ID**: `{sel_alert['asset_id']}` ({sel_alert['asset_type']})")
            st.markdown(f"**Alert Category**: `{sel_alert['alert_type']}`")
            st.markdown(f"**Severity Level**: `{sel_alert['severity']}`")
            st.markdown(f"**Calculated Risk Score**: `{sel_alert['risk_score']:.0f} / 100`")
            st.markdown(f"**Confidence**: `{sel_alert['confidence']*100:.0f}%`")
            st.markdown(f"**Reported Coordinates**: `{sel_alert['reported_position']}`")
            st.markdown(f"**Expected Coordinates**: `{sel_alert['expected_position']}`")

            st.markdown("#### Detected Indicators")
            for ind in sel_alert["detected_indicators"]:
                st.markdown(f"- {ind}")

        with col2:
            st.markdown("#### Trajectory Displacement Vector")
            exp_pos = sel_alert["expected_position"]
            rep_pos = sel_alert["reported_position"]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[exp_pos[1]], y=[exp_pos[0]],
                mode="markers", marker=dict(color="#10b981", size=14, symbol="circle"),
                name="Expected Position"
            ))
            fig.add_trace(go.Scatter(
                x=[rep_pos[1]], y=[rep_pos[0]],
                mode="markers", marker=dict(color="#ef4444", size=16, symbol="x"),
                name="Reported GPS Position"
            ))
            
            fig.add_trace(go.Scatter(
                x=[exp_pos[1], rep_pos[1]],
                y=[exp_pos[0], rep_pos[0]],
                mode="lines", line=dict(color="#ef4444", dash="dash", width=2),
                name="Displacement Vector"
            ))
            
            fig.update_layout(
                title="Geospatial Anomaly Displacement",
                xaxis_title="Longitude",
                yaxis_title="Latitude",
                template="plotly_white",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
