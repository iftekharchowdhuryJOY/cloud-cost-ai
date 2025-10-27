from fastapi import FastAPI
from app.services.cost_explorer import get_spend_timeseries_by_service
from app.ml.anomaly import detect_anomalies_isoforest
from fastapi import Query


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
