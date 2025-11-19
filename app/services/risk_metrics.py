"""Risk metrics calculations for service budgets and spend."""
import pandas as pd
from datetime import datetime, timezone, timedelta
import calendar


def calculate_risk_score(actual: float, budget: float, days_elapsed: int, days_in_month: int) -> dict:
    """
    Calculate comprehensive risk metrics for a service.
    
    Returns:
    {
        "risk_level": "good" | "warning" | "danger",
        "risk_score": 0-100,  # 0 = safest, 100 = most dangerous
        "utilization_pct": 0-100,
        "daily_burn": float,
        "projected_spend": float,
        "days_remaining": int,
        "estimated_overspend": float,  # negative if on track
        "status_icon": "🟢" | "🟡" | "🔴",
    }
    """
    
    if budget <= 0:
        return {
            "risk_level": "no-budget",
            "risk_score": 0,
            "utilization_pct": 0,
            "daily_burn": 0,
            "projected_spend": actual,
            "days_remaining": days_in_month - days_elapsed,
            "estimated_overspend": 0,
            "status_icon": "⚪",
        }
    
    # Calculate metrics
    daily_burn = actual / days_elapsed if days_elapsed > 0 else 0
    projected_spend = daily_burn * days_in_month
    utilization_pct = int((actual / budget) * 100)
    days_remaining = days_in_month - days_elapsed
    estimated_overspend = max(0, projected_spend - budget)
    
    # Calculate risk score (0-100)
    # Based on: utilization rate, burn rate, and projected overspend
    burn_rate_ratio = (daily_burn / (budget / days_in_month)) if budget > 0 else 0
    overspend_ratio = (estimated_overspend / budget) if budget > 0 else 0
    
    risk_score = min(100, int(
        (utilization_pct * 0.4) +  # 40% weight on current utilization
        (burn_rate_ratio * 30) +    # 30% weight on burn rate vs expected
        (overspend_ratio * 30)      # 30% weight on projected overspend
    ))
    
    # Determine risk level
    if utilization_pct >= 100:
        risk_level = "danger"
        status_icon = "🔴"
    elif utilization_pct >= 80 or projected_spend > budget * 1.1:
        risk_level = "warning"
        status_icon = "🟡"
    else:
        risk_level = "good"
        status_icon = "🟢"
    
    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "utilization_pct": utilization_pct,
        "daily_burn": round(daily_burn, 4),
        "projected_spend": round(projected_spend, 2),
        "days_remaining": days_remaining,
        "estimated_overspend": round(estimated_overspend, 2),
        "status_icon": status_icon,
    }


def get_risk_heatmap_data(df: pd.DataFrame, budgets_dict: dict) -> list:
    """
    Generate heatmap data for all services.
    
    Input:
    - df: DataFrame with columns [day, service, cost]
    - budgets_dict: {service: budget_amount}
    
    Output:
    - List of dicts with service risk metrics
    """
    
    today = datetime.now(timezone.utc).date()
    start_of_month = today.replace(day=1)
    days_elapsed = (today - start_of_month).days + 1
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    
    if df.empty:
        return []
    
    # Sum cost per service
    grouped = df.groupby("service")["cost"].sum().reset_index()
    
    heatmap_data = []
    for _, row in grouped.iterrows():
        service = row["service"]
        actual = float(row["cost"])
        budget = budgets_dict.get(service, 0)
        
        risk_metrics = calculate_risk_score(actual, budget, days_elapsed, days_in_month)
        
        heatmap_data.append({
            "service": service,
            "actual_spend": actual,
            "budget": budget,
            **risk_metrics,
        })
    
    # Sort by risk score descending (highest risk first)
    heatmap_data.sort(key=lambda x: x["risk_score"], reverse=True)
    
    return heatmap_data
