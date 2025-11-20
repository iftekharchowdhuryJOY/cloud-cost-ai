from fastapi import APIRouter, Query
from datetime import datetime, timedelta, timezone
import os
import math

from app.services.cost_explorer import get_spend_timeseries_by_service
from app.db.database import SessionLocal
from app.db.service import BudgetService

router = APIRouter()

USE_AWS = os.getenv("USE_AWS", "true").lower() == "true"


@router.get("/costs/services")
async def get_available_services(days: int = Query(default=90, ge=1, le=365)):
    """Get list of all services that have cost data"""
    df = get_spend_timeseries_by_service(days=days)
    
    if df.empty:
        return {"services": []}
    
    services = sorted(df["service"].unique().tolist())
    return {"services": services}


@router.get("/costs/service/{service_name}/trend")
async def get_service_trend(
    service_name: str,
    days: int = Query(default=90, ge=1, le=365),
    ma_window: int = Query(default=7, ge=2, le=30),
    anomaly_factor: float = Query(default=1.5, ge=1.1, le=5.0)
):
    """Get daily spend trend for a specific service.

    Adds:
    - Moving average (window configurable, default 7 days)
    - Simple anomaly flag: cost > anomaly_factor * rolling median (window=ma_window)
    - Budget reference (if configured) from persistent store
    """
    df = get_spend_timeseries_by_service(days=days)
    
    if df.empty:
        return {
            "service": service_name,
            "data": [],
            "summary": {
                "total_spend": 0,
                "avg_daily_spend": 0,
                "days_tracked": 0,
                "trend": "flat"
            }
        }
    
    # Filter for specific service
    service_df = df[df["service"] == service_name].copy()
    
    if service_df.empty:
        return {
            "service": service_name,
            "data": [],
            "summary": {
                "total_spend": 0,
                "avg_daily_spend": 0,
                "days_tracked": 0,
                "trend": "flat"
            }
        }
    
    # Sort by date
    service_df = service_df.sort_values("day")

    # Moving average & rolling median for anomaly detection
    # Use numeric index; ensure float type
    service_df["cost"] = service_df["cost"].astype(float)
    service_df["moving_avg"] = service_df["cost"].rolling(window=ma_window, min_periods=1).mean()
    service_df["rolling_median"] = service_df["cost"].rolling(window=ma_window, min_periods=ma_window//2).median()
    # Anomaly logic: cost > anomaly_factor * rolling_median AND have median value
    service_df["is_anomaly"] = (
        (service_df["rolling_median"].notna()) &
        (service_df["cost"] > service_df["rolling_median"] * anomaly_factor)
    )

    anomaly_days = int(service_df["is_anomaly"].sum())

    # Fetch budget for service (if any)
    db = SessionLocal()
    try:
        budget_obj = BudgetService.get_by_service(db, service_name)
        budget_value = float(budget_obj.budget) if budget_obj else None
    finally:
        db.close()
    
    # Calculate summary metrics
    total_spend = float(service_df["cost"].sum())
    avg_daily = float(service_df["cost"].mean())
    days_tracked = len(service_df)
    
    # Determine trend (compare first half vs second half)
    mid_point = len(service_df) // 2
    if mid_point > 0:
        first_half_avg = service_df.iloc[:mid_point]["cost"].mean()
        second_half_avg = service_df.iloc[mid_point:]["cost"].mean()
        
        if second_half_avg > first_half_avg * 1.1:
            trend = "increasing"
        elif second_half_avg < first_half_avg * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    # Format data for frontend (include moving average & anomaly flag)
    data = []
    anomaly_details = []
    for _, row in service_df.iterrows():
        moving_avg_val = round(float(row["moving_avg"]), 4) if not math.isnan(row["moving_avg"]) else None
        is_anom = bool(row["is_anomaly"])
        rec = {
            "date": row["day"],
            "cost": float(row["cost"]),
            "moving_avg": moving_avg_val,
            "is_anomaly": is_anom,
        }
        data.append(rec)
        if is_anom:
            anomaly_details.append({
                "date": row["day"],
                "cost": float(row["cost"]),
                "moving_avg": moving_avg_val,
                "delta_vs_moving_avg": round(float(row["cost"]) - (moving_avg_val or 0.0), 4)
            })

    last_moving_avg = data[-1]["moving_avg"] if data else None
    
    return {
        "service": service_name,
        "data": data,
        "summary": {
            "total_spend": round(total_spend, 2),
            "avg_daily_spend": round(avg_daily, 2),
            "days_tracked": days_tracked,
            "trend": trend,
            "min_daily": round(float(service_df["cost"].min()), 2),
            "max_daily": round(float(service_df["cost"].max()), 2),
            "moving_avg_window": ma_window,
            "anomaly_days": anomaly_days,
            "budget": budget_value,
            "last_moving_avg": last_moving_avg,
            "anomaly_details": anomaly_details
        }
    }
