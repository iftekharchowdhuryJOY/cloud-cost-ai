from fastapi import FastAPI
from app.services.cost_explorer import get_spend_timeseries_by_service
from app.ml.anomaly import detect_anomalies_isoforest
from fastapi import Query
from app.services.slack_notifier import send_slack_alert
from app.jobs.budget_guard import check_budget_forecast
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Cloud cost optimizer", version="0.1.0")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is alive"}

@app.get("/spend/summary")
def spend_summary(days: int = 30):
    """
    Returns AWS daily cost by service for the given number of days.
    """
    df = get_spend_timeseries_by_service(days=days)
    if df.empty:
        return {"message": "No data returned. Check cost explorer access."}
    result = (
        df.groupby(["day", "service"], as_index=False)["cost"]
        .sum()
        .sort_values(["day", "service"])
        .to_dict(orient="records")
    )
    return {"days": days, "results": result}

# another endpoint: /anomalies would go here
@app.get("/anomalies")
def anomalies(days: int = 120, minImpact: float = 0):
    """
    Detect AI-based cost anomalies and trend breaks.
    """
    df = get_spend_timeseries_by_service(days=days)
    if df.empty:
        return {"anomalies": []}

    scores, flagged, trend_breaks = detect_anomalies_isoforest(df)

    pivot = df.pivot_table(index="day", columns="service", values="cost", aggfunc="sum").fillna(0)
    med   = pivot.rolling(window=7, min_periods=1).median()
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

@app.get("/spend/monthly")
def spend_monthly(months: int = 6):
    df = get_spend_timeseries_by_service(days=30*months)
    df["month"] = pd.to_datetime(df["day"]).dt.to_period("M")
    monthly = df.groupby("month", as_index=False)["cost"].sum()
    return monthly.to_dict(orient="records")

@app.get("/anomalies/notify")
def anomalies_notify(days: int = 120, minImpact: float = 0.1):
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

@app.get("/forecast/budget")
def forecast_budget_check():
    """
    Manually trigger a predictive budget forecast check.
    Returns the forecasted next-day spend and whether it breaches the budget.
    """
    from datetime import datetime, timedelta
    import pandas as pd
    from app.ml.forecast import train_and_forecast

    r = requests.get(f"{API_BASE}/spend/summary?days=90")
    df = pd.DataFrame(r.json()["results"])
    if df.empty:
        return {"status": "no_data", "message": "No cost data available."}

    forecast = train_and_forecast(df, 7)
    tomorrow = datetime.utcnow().date() + timedelta(days=1)
    tomorrow_row = forecast[forecast["ds"].dt.date == tomorrow]

    if tomorrow_row.empty:
        return {"status": "no_forecast", "message": "No forecast for tomorrow."}

    pred = float(tomorrow_row["yhat"].values[0])
    breach = pred > BUDGET_LIMIT
    if breach:
        send_slack_alert(f"⚠️ Predicted spend for tomorrow is ${pred:.2f} (> ${BUDGET_LIMIT:.2f})")

    return {
        "forecast_date": str(tomorrow),
        "predicted_usd": round(pred, 2),
        "budget_limit_usd": BUDGET_LIMIT,
        "breach": breach
    }