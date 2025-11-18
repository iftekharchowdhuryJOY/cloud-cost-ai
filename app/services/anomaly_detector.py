import pandas as pd
from .cost_explorer import get_spend_timeseries_by_service

def detect_anomalies(start: str, end: str, threshold: float = 1.3):
    """
    Simple anomaly detection:
    - Aggregate cost per day
    - Compute rolling baseline
    - Compare daily cost vs baseline
    - Return anomaly rows
    """
    df = get_spend_timeseries_by_service(start=start, end=end)

    if df.empty:
        return []

    # Total daily spend
    daily = (
        df.groupby("day")["cost"]
        .sum()
        .reset_index()
        .sort_values("day")
    )

    # Compute rolling 7-day baseline
    daily["baseline"] = daily["cost"].rolling(window=7, min_periods=1).mean()

    anomalies = []
    for _, row in daily.iterrows():
        day = str(row["day"])
        cost = float(row["cost"])
        baseline = float(row["baseline"])

        # Skip very small costs
        if baseline < 0.000001:
            continue

        if cost > baseline * threshold:
            deviation_pct = ((cost - baseline) / baseline) * 100

            anomalies.append({
                "day": day,
                "cost": cost,
                "baseline": baseline,
                "deviation_pct": round(deviation_pct, 2),
            })

    return anomalies
