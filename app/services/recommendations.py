import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timezone

from app.services.cost_explorer import get_spend_timeseries_by_service
from app.db.database import SessionLocal
from app.db.service import BudgetService

USE_AWS = os.getenv("USE_AWS", "true").lower() == "true"


@dataclass
class Issue:
    code: str
    title: str
    evidence: str
    recommended_action: str
    potential_savings_usd: Optional[float] = None


def _rolling_median_anomalies(series: pd.Series, window: int = 7, factor: float = 1.5) -> pd.Series:
    med = series.rolling(window=window, min_periods=max(2, window//2)).median()
    return (series > med * factor) & med.notna()


def _service_features(s_df: pd.DataFrame, budget: Optional[float]) -> Dict[str, Any]:
    s = s_df.sort_values("day").copy()
    s_cost = s["cost"].astype(float)

    total_spend = float(s_cost.sum())
    avg_daily = float(s_cost.mean()) if len(s_cost) else 0.0
    std_daily = float(s_cost.std(ddof=0)) if len(s_cost) else 0.0
    volatility_ratio = float(std_daily / (avg_daily + 1e-6)) if avg_daily > 0 else 0.0

    last7 = float(s_cost.tail(7).mean()) if len(s_cost) else 0.0
    prev21 = float(s_cost.iloc[:-7].tail(21).mean()) if len(s_cost) > 7 else 0.0
    acceleration_ratio = (last7 / (prev21 + 1e-6)) if prev21 > 0 else 1.0

    # anomaly density via rolling median
    anom_flags = _rolling_median_anomalies(s_cost, window=7, factor=1.5)
    anomaly_density = float(anom_flags.mean()) if len(s_cost) else 0.0

    # recent change pct vs 7d MA
    ma7 = s_cost.rolling(window=7, min_periods=1).mean()
    recent_change_pct = float(((s_cost.iloc[-1] if len(s_cost) else 0.0) - (ma7.iloc[-1] if len(ma7) else 0.0)) / ((ma7.iloc[-1] if len(ma7) else 0.0) + 1e-6)) if len(s_cost) else 0.0

    # simple projection: next 30 days using recent 14d avg if available, else overall avg
    ref_avg = float(s_cost.tail(14).mean()) if len(s_cost) >= 14 else avg_daily
    projected_30d = ref_avg * 30.0
    budget_pressure = (projected_30d / budget) if (budget and budget > 0) else None

    return {
        "total_spend": round(total_spend, 2),
        "avg_daily": round(avg_daily, 2),
        "std_daily": round(std_daily, 2),
        "volatility_ratio": round(volatility_ratio, 3),
        "acceleration_ratio": round(acceleration_ratio, 3),
        "anomaly_density": round(anomaly_density, 3),
        "recent_change_pct": round(recent_change_pct, 3),
        "projected_30d": round(projected_30d, 2),
        "budget": budget,
        "budget_pressure": round(budget_pressure, 3) if budget_pressure is not None else None,
        "days_tracked": int(len(s_cost)),
    }


def _issue_rules(service: str, f: Dict[str, Any]) -> List[Issue]:
    issues: List[Issue] = []

    if f.get("budget") and f.get("budget_pressure") and f["budget_pressure"] > 1.0:
        over = f["projected_30d"] - (f["budget"] or 0)
        issues.append(Issue(
            code="BUDGET_RISK",
            title="Projected budget breach",
            evidence=f"Projected 30d ${f['projected_30d']:.2f} vs budget ${f['budget']:.2f} (pressure {f['budget_pressure']:.2f}x)",
            recommended_action="Reduce spend or raise budget; review top drivers for this service.",
            potential_savings_usd=round(over, 2)
        ))

    if f.get("acceleration_ratio", 1) > 1.25:
        issues.append(Issue(
            code="RAPID_GROWTH",
            title="Spend accelerating week-over-week",
            evidence=f"Last 7d avg is {f['acceleration_ratio']:.2f}x the prior 3 weeks",
            recommended_action="Investigate recent deployments or usage spikes; set alerts if intentional growth."
        ))

    if f.get("anomaly_density", 0) > 0.15:
        issues.append(Issue(
            code="FREQUENT_ANOMALIES",
            title="Frequent anomalous days",
            evidence=f"{int(f['anomaly_density']*100)}% of days flagged vs rolling median",
            recommended_action="Drill into daily spikes; add guardrails and cost caps."
        ))

    if f.get("volatility_ratio", 0) > 0.5 and f.get("avg_daily", 0) > 0.5:
        issues.append(Issue(
            code="HIGH_VOLATILITY",
            title="High cost volatility",
            evidence=f"Std/Mean = {f['volatility_ratio']:.2f} on avg daily ${f['avg_daily']:.2f}",
            recommended_action="Stabilize usage patterns; consider commitments only after stabilization."
        ))

    if f.get("recent_change_pct", 0) < -0.3:
        issues.append(Issue(
            code="COST_DROP",
            title="Recent cost drop — validate downsizing",
            evidence=f"Last day is {abs(f['recent_change_pct'])*100:.1f}% below 7d average",
            recommended_action="If performance is stable, rightsize or deprovision redundant resources."
        ))

    return issues


def _priority_score(f: Dict[str, Any]) -> int:
    # Weighted composite, capped and normalized roughly to 0..100
    bp = min((f.get("budget_pressure") or 0), 2.0) / 2.0  # 0..1
    acc = min(f.get("acceleration_ratio", 1.0) - 1.0, 1.0)  # 0..1 when 2x
    an = min(f.get("anomaly_density", 0.0), 0.5) * 2       # 0..1 when 50%
    vol = min(f.get("volatility_ratio", 0.0), 1.0)         # 0..1
    score = 0.35*bp + 0.35*acc + 0.2*an + 0.1*vol
    return int(round(score * 100))


def generate_recommendations(days: int = 90) -> Dict[str, Any]:
    df = get_spend_timeseries_by_service(days=days)
    if df.empty:
        return {"data": [], "summary": {"services_evaluated": 0, "recommendations": 0, "potential_savings_total": 0.0}}

    df["day"] = pd.to_datetime(df["day"]).dt.date

    db = SessionLocal()
    try:
        recs = []
        for service, s_df in df.groupby("service"):
            budget_obj = BudgetService.get_by_service(db, service)
            budget = float(budget_obj.budget) if budget_obj else None
            f = _service_features(s_df, budget)
            issues = _issue_rules(service, f)
            priority = _priority_score(f)
            potential = sum([i.potential_savings_usd or 0.0 for i in issues])
            if not issues:
                continue
            recs.append({
                "service": service,
                "features": f,
                "issues": [i.__dict__ for i in issues],
                "priority_score": priority,
                "potential_savings_usd": round(potential, 2)
            })
    finally:
        db.close()

    recs = sorted(recs, key=lambda r: r["priority_score"], reverse=True)
    summary = {
        "services_evaluated": int(df["service"].nunique()),
        "recommendations": len(recs),
        "potential_savings_total": round(sum(r["potential_savings_usd"] for r in recs), 2)
    }
    return {"data": recs, "summary": summary}


def explain_recommendation(service: str, days: int = 90) -> Dict[str, Any]:
    df = get_spend_timeseries_by_service(days=days)
    if df.empty:
        return {"service": service, "explanation": "No cost data available.", "facts": {}}
    s_df = df[df["service"] == service]
    if s_df.empty:
        return {"service": service, "explanation": "Service not found in selected window.", "facts": {}}

    db = SessionLocal()
    try:
        budget_obj = BudgetService.get_by_service(db, service)
        budget = float(budget_obj.budget) if budget_obj else None
    finally:
        db.close()

    f = _service_features(s_df, budget)
    issues = _issue_rules(service, f)
    if not issues:
        return {"service": service, "explanation": "No issues detected for this service.", "facts": f}

    top = issues[0]
    explanation = (
        f"{service} shows {top.title.lower()}. {top.evidence}. "
        f"Recommendation: {top.recommended_action}"
    )
    return {"service": service, "explanation": explanation, "facts": f, "issues": [i.__dict__ for i in issues]}
