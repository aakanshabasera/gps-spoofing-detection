import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any


def render_analytics_panel(df: pd.DataFrame, alerts: List[Dict[str, Any]], eval_results: Dict[str, Any] = None):
    """
    Renders analytics charts, time-series kinematic graphs, and model evaluation metrics
    in a clean corporate light design.
    """
    st.subheader("Historical Analytics & Detection Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Alerts by Severity Level")
        if alerts:
            sev_counts = pd.DataFrame(alerts)["severity"].value_counts().reset_index()
            sev_counts.columns = ["Severity", "Count"]
            fig_sev = px.bar(
                sev_counts, x="Severity", y="Count",
                color="Severity",
                color_discrete_map={"CRITICAL": "#ef4444", "HIGH": "#f97316", "MEDIUM": "#eab308", "LOW": "#3b82f6"},
                template="plotly_white"
            )
            st.plotly_chart(fig_sev, use_container_width=True)
        else:
            st.info("No active alerts recorded.")
            
    with col2:
        st.markdown("#### Alerts by Anomaly Category")
        if alerts:
            type_counts = pd.DataFrame(alerts)["alert_type"].value_counts().reset_index()
            type_counts.columns = ["Anomaly Category", "Count"]
            fig_type = px.pie(
                type_counts, names="Anomaly Category", values="Count",
                hole=0.4, template="plotly_white"
            )
            st.plotly_chart(fig_type, use_container_width=True)
        else:
            st.info("No anomaly categories recorded.")

    # Telemetry Kinematic Graphs
    if df is not None and not df.empty:
        st.markdown("#### Dynamic Kinematics Time-Series Analysis")
        
        fig_speed = go.Figure()
        fig_speed.add_trace(go.Scatter(
            x=df["timestamp"], y=df["speed_kts"],
            mode="lines+markers", name="Reported Speed (kts)",
            line=dict(color="#2563eb", width=2)
        ))
        
        if "is_spoofed" in df.columns:
            spoofed_mask = df["is_spoofed"] == True
            if spoofed_mask.any():
                fig_speed.add_trace(go.Scatter(
                    x=df[spoofed_mask]["timestamp"], y=df[spoofed_mask]["speed_kts"],
                    mode="markers", name="Ground-Truth Spoofed",
                    marker=dict(color="#ef4444", size=8, symbol="x")
                ))
                
        fig_speed.update_layout(
            title="Speed Profile over Time",
            xaxis_title="Timestamp (seconds)",
            yaxis_title="Speed (knots)",
            template="plotly_white"
        )
        st.plotly_chart(fig_speed, use_container_width=True)

    # Evaluation Metrics Table
    if eval_results:
        st.markdown("#### Detection Algorithm Performance Benchmark")
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Accuracy", f"{eval_results['accuracy']*100:.1f}%")
        m2.metric("Precision", f"{eval_results['precision']*100:.1f}%")
        m3.metric("Recall", f"{eval_results['recall']*100:.1f}%")
        m4.metric("F1-Score", f"{eval_results['f1_score']*100:.1f}%")
        m5.metric("False Positive Rate", f"{eval_results['false_positive_rate']*100:.1f}%")
        m6.metric("Latency", f"{eval_results['detection_latency_sec']}s" if eval_results.get('detection_latency_sec') is not None else "N/A")
