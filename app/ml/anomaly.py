import pandas as pd
from sklearn.ensemble import IsolationForest

def detect_anomalies_isoforest(df: pd.DataFrame, contamination=0.15):
    """
    Detect day-level anomalies via IsolationForest.
    Also flag sudden trend breaks (drop or rise >50% vs previous 7-day mean).
    """
    pivot = df.pivot_table(index="day", columns="service", values="cost", aggfunc="sum").fillna(0)
    if pivot.shape[0] < 10:
        return {}, [], []

    model = IsolationForest(contamination=contamination, random_state=42)
    model.fit(pivot.values)
    scores = model.decision_function(pivot.values)
    threshold = pd.Series(scores).quantile(0.10)
    flagged_idx = [i for i, s in enumerate(scores) if s <= threshold]
    flagged_days = [pivot.index[i] for i in flagged_idx]

    # --- Trend break detection ---
    total = pivot.sum(axis=1)
    prev_mean = total.rolling(window=7, min_periods=3).mean()
    change = (total - prev_mean) / (prev_mean + 1e-6)
    trend_breaks = total[abs(change) > 0.5].index.tolist()  # ±50 %

    score_map = {pivot.index[i]: float(scores[i]) for i in range(len(scores))}
    return score_map, flagged_days, trend_breaks
