import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.services.cost_explorer import get_spend_timeseries_by_service
from app.db.database import SessionLocal
from app.db.service import BudgetService, FeedbackService, AlertService, RecoveryService, SettingsService
from app.services.slack_notifier import send_slack_alert

USE_AWS = os.getenv("USE_AWS", "true").lower() == "true"

# Feedback scoring tunables (env overrideable)
def _load_settings(db) -> dict:
    raw = SettingsService.get_all(db)
    return {
        "FEEDBACK_DISMISS_COOLDOWN_DAYS": int(raw.get("FEEDBACK_DISMISS_COOLDOWN_DAYS", 14)),
        "FEEDBACK_ACCEPT_BOOST": int(raw.get("FEEDBACK_ACCEPT_BOOST", 15)),
        "FEEDBACK_DISMISS_PENALTY_FACTOR": float(raw.get("FEEDBACK_DISMISS_PENALTY_FACTOR", 0.4)),
        "RECOMMENDATION_ALERT_THRESHOLD": int(raw.get("RECOMMENDATION_ALERT_THRESHOLD", 70)),
        "RECOMMENDATION_ALERT_COOLDOWN_DAYS": int(raw.get("RECOMMENDATION_ALERT_COOLDOWN_DAYS", 7)),
        "RECOMMENDATION_RECOVERY_DAYS": int(raw.get("RECOMMENDATION_RECOVERY_DAYS", 3)),
    }


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


def _apply_feedback_adjustment(service: str, features: Dict[str, Any], base_score: int, db, settings: dict) -> Dict[str, Any]:
    """Adjust priority based on most recent feedback.

    - Dismiss: suppress score for cooldown window
    - Accept: boost score while problematic signals persist (acceleration, anomalies, budget pressure)
    """
    rows = FeedbackService.recent_for_service(db, service, limit=1)
    if not rows:
        return {
            "priority_score": base_score,
            "base_priority_score": base_score,
            "feedback_action": None,
            "feedback_effect": None,
        }
    fb = rows[0]
    # Normalize created_at to UTC aware
    def _utc(dt):
        if not dt:
            return None
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    now_utc = datetime.now(timezone.utc)
    fb_created = _utc(fb.created_at)
    age_days = (now_utc - fb_created).days if fb_created else 0

    action = fb.action
    adjusted = base_score
    effect_desc = None

    if action == "dismiss" and age_days <= settings["FEEDBACK_DISMISS_COOLDOWN_DAYS"]:
        adjusted = int(round(base_score * settings["FEEDBACK_DISMISS_PENALTY_FACTOR"]))
        effect_desc = f"Suppressed after dismiss {age_days}d ago (cooldown {settings['FEEDBACK_DISMISS_COOLDOWN_DAYS']}d)."
    elif action == "accept":
        # Determine if issue still persists (cost acceleration, anomaly density, or budget pressure high)
        persists = (
            (features.get("acceleration_ratio", 1.0) > 1.05)
            or (features.get("anomaly_density", 0.0) > 0.05)
            or (features.get("budget_pressure") and features.get("budget_pressure") > 1.0)
        )
        if persists:
            adjusted = min(100, base_score + settings["FEEDBACK_ACCEPT_BOOST"])
            effect_desc = f"Boosted (+{settings['FEEDBACK_ACCEPT_BOOST']}) after accept {age_days}d ago; issue persists."
        else:
            effect_desc = f"Not boosted: conditions improved since accept {age_days}d ago."

    return {
        "priority_score": adjusted,
        "base_priority_score": base_score,
        "feedback_action": action,
        "feedback_effect": effect_desc,
    }


def generate_recommendations(days: int = 90) -> Dict[str, Any]:
    df = get_spend_timeseries_by_service(days=days)
    if df.empty:
        return {"data": [], "summary": {"services_evaluated": 0, "recommendations": 0, "potential_savings_total": 0.0}}

    df["day"] = pd.to_datetime(df["day"]).dt.date

    db = SessionLocal()
    try:
        recs = []
        settings = _load_settings(db)
        for service, s_df in df.groupby("service"):
            budget_obj = BudgetService.get_by_service(db, service)
            budget = float(budget_obj.budget) if budget_obj else None
            f = _service_features(s_df, budget)
            issues = _issue_rules(service, f)
            priority = _priority_score(f)
            # Savings estimation: if projected spend exceeds budget, apply acceleration factor
            potential = 0.0
            if budget and f.get("projected_30d") and f["projected_30d"] > budget:
                raw_over = f["projected_30d"] - budget
                accel_excess = max(0.0, f.get("acceleration_ratio", 1.0) - 1.0)  # 0 for <=1
                potential = round(raw_over * (1 + accel_excess), 2)
            # If BUDGET_RISK issue exists with its own potential_savings_usd, prefer max between calculated and issue value
            issue_potential_sum = sum([(i.potential_savings_usd or 0.0) for i in issues])
            potential = max(potential, issue_potential_sum)
            if not issues:
                continue
            adj = _apply_feedback_adjustment(service, f, priority, db, settings)
            # Slack alert on first high-priority appearance (with cooldown) & recovery detection
            alert_sent = False
            alert_recovered = False
            if adj["priority_score"] >= settings["RECOMMENDATION_ALERT_THRESHOLD"]:
                if not AlertService.has_recent_alert(db, service, settings["RECOMMENDATION_ALERT_COOLDOWN_DAYS"]):
                    title = f"High-Priority Cost Recommendation: {service}"
                    msg_lines = [
                        f"Priority {adj['priority_score']} (base {adj['base_priority_score']})",
                        f"Issues: {', '.join([i.code for i in issues])}"
                    ]
                    if f.get("budget_pressure"):
                        msg_lines.append(f"Budget pressure: {f['budget_pressure']:.2f}x")
                    if f.get("acceleration_ratio"):
                        msg_lines.append(f"Acceleration: {f['acceleration_ratio']:.2f}x")
                    if f.get("anomaly_density"):
                        msg_lines.append(f"Anomaly density: {f['anomaly_density']*100:.0f}%")
                    slack_msg = "\n".join(msg_lines)
                    if send_slack_alert(title, slack_msg, emoji="🚨"):
                        AlertService.record_alert(db, service, adj["priority_score"], adj["base_priority_score"], adj["feedback_action"])
                        alert_sent = True
            else:
                # Below threshold: check for recovery from prior high alert
                from app.db.models import RecommendationAlert
                latest_alert = (
                    db.query(RecommendationAlert)
                    .filter(RecommendationAlert.service == service)
                    .order_by(RecommendationAlert.created_at.desc())
                    .first()
                )
                if latest_alert and latest_alert.priority_score >= settings["RECOMMENDATION_ALERT_THRESHOLD"]:
                    age_days = (datetime.now(timezone.utc) - (latest_alert.created_at if latest_alert.created_at.tzinfo else latest_alert.created_at.replace(tzinfo=timezone.utc))).days
                    if age_days >= settings["RECOMMENDATION_RECOVERY_DAYS"]:
                        alert_recovered = True
                        send_slack_alert(
                            f"Recommendation Recovered: {service}",
                            f"Priority now {adj['priority_score']} (< {settings['RECOMMENDATION_ALERT_THRESHOLD']}) after {age_days}d.",
                            emoji="✅"
                        )
                        RecoveryService.record_recovery(db, service, latest_alert.priority_score, adj["priority_score"], age_days)
            recs.append({
                "service": service,
                "features": f,
                "issues": [i.__dict__ for i in issues],
                "priority_score": adj["priority_score"],
                "base_priority_score": adj["base_priority_score"],
                "feedback_action": adj["feedback_action"],
                "feedback_effect": adj["feedback_effect"],
                "alert_sent": alert_sent,
                "alert_recovered": alert_recovered,
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
        fb_rows = FeedbackService.recent_for_service(db, service, limit=1)
    finally:
        db.close()

    f = _service_features(s_df, budget)
    issues = _issue_rules(service, f)
    if not issues:
        return {"service": service, "explanation": "No issues detected for this service.", "facts": f}

    top = issues[0]
    explanation = (
        f"{service} shows {top.title.lower()}. {top.evidence}. "
        f"Recommendation: {top.recommended_action}."
    )
    if fb_rows:
        fb = fb_rows[0]
        fb_created = fb.created_at if fb.created_at and fb.created_at.tzinfo else (fb.created_at.replace(tzinfo=timezone.utc) if fb.created_at else None)
        age_days = (datetime.now(timezone.utc) - fb_created).days if fb_created else 0
        explanation += f" Last feedback: {fb.action} {age_days}d ago."
    return {"service": service, "explanation": explanation, "facts": f, "issues": [i.__dict__ for i in issues], "feedback": fb_rows[0].to_dict() if fb_rows else None}
