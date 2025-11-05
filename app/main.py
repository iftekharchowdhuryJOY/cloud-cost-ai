from fastapi import FastAPI, Query
from dotenv import load_dotenv
import os
import logging
import pandas as pd

from app.services.cost_explorer import get_spend_timeseries_by_service
from app.ml.anomaly import detect_anomalies_isoforest
from app.services.slack_notifier import send_slack_alert
from app.jobs.budget_guard import check_budget_forecast

load_dotenv()

app = FastAPI(title="Cloud Cost Optimizer", version="0.1.0")

# --- Global Settings ---
USE_AWS = os.getenv("USE_AWS", "true").lower() == "true"
BUDGET_LIMIT = float(os.getenv("BUDGET_LIMIT", "10.00"))

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("cloud-cost-optimizer")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is alive", "safe_mode": not USE_AWS}

@app.get("/spend/summary")
def spend_summary(days: int = 30):
    df = get_spend_timeseries_by_service(days=days)
    if df.empty:
        return {"message": "SAFE MODE: No data fetched from AWS.", "results": []}
    result = (
        df.groupby(["day", "service"], as_index=False)["cost"]
        .sum()
        .sort_values(["day", "service"])
        .to_dict(orient="records")
    )
    return {"days": days, "results": result}

@app.get("/anomalies")
def anomalies(days: int = 120, minImpact: float = 0):
    df = get_spend_timeseries_by_service(days=days)
    if df.empty:
        return {"anomalies": [], "message": "SAFE MODE active — no anomalies."}

    scores, flagged, trend_breaks = detect_anomalies_isoforest(df)

    pivot = df.pivot_table(index="day", columns="service", values="cost", aggfunc="sum").fillna(0)
    med = pivot.rolling(window=7, min_periods=1).median()
    delta = (pivot - med).clip(lower=0).sum(axis=1)

    results = []
    for d in flagged + trend_breaks:
        if d not in pivot.index:
            continue
        impact = float(delta.get(d, 0))
        if impact < minImpact and d not in trend_breaks:
            continue
        top_svc = (pivot.loc[d] - med.loc[d]).fillna(0).nlargest(3)
        results.append({
            "day": str(d),
            "impact_usd": round(impact, 3),
            "top_services": [
                {"name": s, "delta_usd": round(v, 3)} for s, v in top_svc.items() if v > 0
            ],
            "type": "trend_break" if d in trend_breaks else "anomaly",
            "score": float(scores.get(d, 0))
        })
    results.sort(key=lambda x: x["impact_usd"], reverse=True)
    return {"lookback_days": days, "count": len(results), "results": results}

@app.get("/anomalies/notify")
def anomalies_notify(days: int = 120, minImpact: float = 0.1):
    if not USE_AWS:
        return {"status": "SAFE_MODE", "message": "AWS API disabled."}

    data = anomalies(days=days, minImpact=minImpact)
    results = data["results"]
    if not results:
        return {"status": "no anomalies"}

    latest = results[0]
    msg = (
        f"• Date: {latest['day']}\n"
        f"• Impact: ${latest['impact_usd']}\n"
        + "\n".join([f"• {s['name']}: +${s['delta_usd']}" for s in latest["top_services"]])
    )
    send_slack_alert("AWS Cost Anomaly Detected", msg, "🚨")
    return {"status": "sent", "alert": latest}

# --- Disable Scheduler in SAFE MODE ---
if USE_AWS:
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_budget_forecast, "interval", hours=1)
    scheduler.start()
else:
    print("⚠️ SAFE MODE ENABLED — Scheduler not started.")
