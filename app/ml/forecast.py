# app/ml/forecast.py
import pandas as pd
from prophet import Prophet
from datetime import datetime, timedelta

def train_and_forecast(df: pd.DataFrame, forecast_days: int = 7):
    """
    Train Prophet model on daily AWS cost data and forecast future spend.

    Parameters:
        df (pd.DataFrame): columns ['day', 'cost']
        forecast_days (int): number of future days to forecast

    Returns:
        pd.DataFrame: Prophet forecast dataframe with ['ds','yhat','yhat_lower','yhat_upper']
    """
    if df.empty:
        raise ValueError("Empty DataFrame: no cost data for forecasting.")

    df = df.copy()
    df["day"] = pd.to_datetime(df["day"])
    daily = df.groupby("day")["cost"].sum().reset_index()
    daily.columns = ["ds", "y"]

    model = Prophet(interval_width=0.9)
    model.fit(daily)
    future = model.make_future_dataframe(periods=forecast_days)
    forecast = model.predict(future)

    return forecast
