import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from slack_ui import slack_trigger_tab
from forecast import forecast_tab

API_BASE = "http://localhost:8080"

st.set_page_config(page_title="Cloud Cost AI Dashboard", layout="wide")

st.title("☁️ Cloud Cost AI Dashboard")
st.caption("Real-time AWS Cost Insights + AI Forecast + Slack Control")

tab1, tab2, tab3 = st.tabs(["💵 Spend Overview", "⚠️ Anomalies", "🚨 Slack / Forecast"])

# ---------- Spend Overview ----------
with tab1:
    days = st.number_input("Days to look back", 7, 180, 30)
    r = requests.get(f"{API_BASE}/spend/summary?days={days}")
    data = r.json()["results"]
    df = pd.DataFrame(data)
    if df.empty:
        st.warning("No cost data found.")
    else:
        df["day"] = pd.to_datetime(df["day"])
        pivot = df.pivot(index="day", columns="service", values="cost").fillna(0)
        fig = px.area(pivot, x=pivot.index, y=pivot.columns, title="Daily AWS Spend by Service ($)")
        st.plotly_chart(fig, use_container_width=True)
        today = df[df["day"] == df["day"].max()]
        st.subheader(f"📅 Today ({df['day'].max().date()})")
        st.dataframe(today.sort_values("cost", ascending=False).reset_index(drop=True))

# ---------- Anomalies ----------
with tab2:
    days = st.number_input("Anomaly days", 7, 180, 120, key="anomaly_days")
    minImpact = st.number_input("Min Impact ($)", 0.0, 50.0, 0.1, key="minimpact")
    r = requests.get(f"{API_BASE}/anomalies?days={days}&minimpact={minImpact}")
    anomalies = r.json()["results"]
    if not anomalies:
        st.info("No anomalies detected in this period.")
    else:
        dfA = pd.DataFrame(anomalies)
        dfA["day"] = pd.to_datetime(dfA["day"])
        st.dataframe(dfA[["day", "impact_usd", "type", "score"]])
        heat = dfA.groupby("day")["impact_usd"].sum().reset_index()
        fig2 = px.density_heatmap(heat, x="day", y="impact_usd", color_continuous_scale="Reds",
                                  title="Anomaly Impact Heatmap")
        st.plotly_chart(fig2, use_container_width=True)

# ---------- Slack & Forecast ----------
with tab3:
    slack_trigger_tab()
    st.divider()
    forecast_tab()
