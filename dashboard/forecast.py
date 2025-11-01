import pandas as pd
import streamlit as st
import plotly.express as px
import requests
from datetime import datetime, timedelta

try:
    from prophet import Prophet
    MODEL = "prophet"
except ImportError:
    from statsmodels.tsa.arima.model import ARIMA
    MODEL = "arima"

API_BASE = "http://localhost:8080"

@st.cache_data(ttl=600)
def get_summary(days):
    r = requests.get(f"{API_BASE}/spend/summary?days={days}")
    data = r.json()["results"]
    return pd.DataFrame(data)

def forecast_tab():
    st.header("📈 AWS Cost Forecast (Next 7 Days)")
    days = st.number_input("History (days)", 30, 180, 90)

    df = get_summary(days)
    if df.empty:
        st.warning("No data available for forecast.")
        return

    df["day"] = pd.to_datetime(df["day"])
    daily = df.groupby("day")["cost"].sum().reset_index()
    daily.columns = ["ds", "y"]

    if MODEL == "prophet":
        model = Prophet(interval_width=0.9)
        model.fit(daily)
        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)
        fig = px.line(forecast, x="ds", y="yhat", title="Forecasted AWS Spend (Prophet)")
        fig.add_scatter(x=daily["ds"], y=daily["y"], mode="lines", name="Actual")
    else:
        model = ARIMA(daily["y"], order=(2,1,1)).fit()
        forecast_vals = model.forecast(7)
        forecast_dates = [daily["ds"].iloc[-1] + timedelta(days=i+1) for i in range(7)]
        forecast = pd.DataFrame({"ds": forecast_dates, "yhat": forecast_vals})
        fig = px.line(forecast, x="ds", y="yhat", title="Forecasted AWS Spend (ARIMA)")
        fig.add_scatter(x=daily["ds"], y=daily["y"], mode="lines", name="Actual")

    st.plotly_chart(fig, use_container_width=True)
    st.info(f"Model used: {MODEL.upper()}")
