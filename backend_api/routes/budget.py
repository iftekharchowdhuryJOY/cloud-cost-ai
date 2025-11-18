from fastapi import APIRouter
from datetime import datetime, timezone, timedelta
import calendar
from app.services.cost_explorer import get_spend_timeseries_by_service

router = APIRouter(tags=["budget"])

@router.get("/budget")
def budget_analysis(budget: float):
    """
    Calculate month-to-date spend, burn rate, and projected end-of-month spend.
    budget: user-defined monthly budget
    """

    today = datetime.now(timezone.utc).date()
    start_of_month = today.replace(day=1)
    days_elapsed = (today - start_of_month).days + 1

    df = get_spend_timeseries_by_service(days=days_elapsed)

    if df.empty:
        return {
            "data": {
                "actual_spend": 0,
                "burn_rate": 0,
                "projected_spend": 0,
                "status": "no-data"
            }
        }

    # Total spend month-to-date
    actual = df["cost"].sum()

    # Burn rate per day
    burn_rate = actual / days_elapsed

    # Project end-of-month spend
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    projected = burn_rate * days_in_month

    # Status
    if projected > budget:
        status = "danger"        # 🔴 over budget
    elif projected > budget * 0.9:
        status = "warning"       # 🟡 at risk
    else:
        status = "good"          # 🟢 on track

    return {
        "data": {
            "actual_spend": round(actual, 4),
            "burn_rate": round(burn_rate, 4),
            "projected_spend": round(projected, 4),
            "budget_limit": budget,
            "status": status,
            "days_elapsed": days_elapsed,
            "days_in_month": days_in_month,
        }
    }
