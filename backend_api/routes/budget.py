from fastapi import APIRouter
from datetime import datetime, timezone
import calendar
import json
import pathlib
import hashlib

from app.services.cost_explorer import get_spend_timeseries_by_service
from app.services.slack_notifier import send_slack_alert

router = APIRouter(tags=["budget"])

# ------------------------------------------
# 🔧 Deduplication: Track last alert sent
# ------------------------------------------
STATE_DIR = pathlib.Path(".state")
STATE_DIR.mkdir(exist_ok=True)
BUDGET_STATE_FILE = STATE_DIR / "budget_alert_state.json"


def load_budget_state():
    """Load the last alert signature to avoid duplicates."""
    if BUDGET_STATE_FILE.exists():
        return json.loads(BUDGET_STATE_FILE.read_text())
    return {"last_alert_hash": None, "last_alert_time": None}


def save_budget_state(state):
    """Save the alert signature."""
    BUDGET_STATE_FILE.write_text(json.dumps(state))


def hash_alert(status, actual, projected, budget):
    """Create a signature for the alert to detect duplicates."""
    payload = f"{status}:{actual:.2f}:{projected:.2f}:{budget:.2f}"
    return hashlib.md5(payload.encode()).hexdigest()

# ------------------------------------------
# 🔥 Per-Service Monthly Budgets (Adjust freely)
# ------------------------------------------
SERVICE_BUDGETS = {
    "AmazonEC2": 0.01,
    "Amazon Simple Storage Service": 0.01,
    "AWS Lambda": 0.5,
    "AmazonNATGateway": 0.0003,
    "AWS Cost Explorer": 0.30,
}


# ------------------------------------------
# 🔧 Build per-service budget rows for frontend table
# ------------------------------------------
def build_service_budget_rows(df, days_elapsed: int, days_in_month: int):
    if df.empty:
        return []

    rows = []
    grouped = df.groupby("service")["cost"].sum().reset_index()

    print(f"🔍 Processing {len(grouped)} services for budget check:")
    
    for _, row in grouped.iterrows():
        service = row["service"]
        actual = float(row["cost"])

        # daily burn
        daily_burn = actual / days_elapsed
        projected = daily_burn * days_in_month

        budget = SERVICE_BUDGETS.get(service)

        print(f"  - {service}: actual=${actual:.4f}, projected=${projected:.4f}, budget={budget}")

        # Determine service status
        if budget is None:
            status = "no-budget"
        else:
            if projected <= 0.9 * budget:
                status = "good"
            elif projected <= budget:
                status = "warning"
            else:
                status = "danger"
                print(f"    ⚠️ DANGER! {service} exceeded!")

                # 🔥 Send Slack alert for only THIS service
                print(f"🔥 Service {service} alert: projected ${projected:.4f} > budget ${budget:.4f}")
                send_slack_alert(
                    f"{service} Budget Alert",
                    (
                        f"*{service}* is projected to exceed its budget.\n"
                        f"• Actual: ${actual:.2f}\n"
                        f"• Budget: ${budget:.2f}\n"
                        f"• Projected: ${projected:.2f}\n"
                        f"• Days elapsed: {days_elapsed}/{days_in_month}"
                    ),
                    emoji="🔥"
                )

        rows.append({
            "service": service,
            "actual_spend": round(actual, 2),
            "projected_spend": round(projected, 2),
            "budget": round(budget, 2) if budget is not None else None,
            "status": status,
        })

    return rows


# ------------------------------------------
# 🔥 Main Budget Endpoint
# ------------------------------------------
@router.get("/budget")
def budget_analysis(budget: float, force: bool = False):
    """
    Calculates:
    - MTD spend
    - Burn rate
    - Monthly projection
    - Budget status
    - Per-service budgets (NEW)
    
    Parameters:
    - budget: Monthly budget limit (USD)
    - force: If True, bypass deduplication and send alert anyway (for testing)
    """

    today = datetime.now(timezone.utc).date()
    start_of_month = today.replace(day=1)
    days_elapsed = (today - start_of_month).days + 1
    days_in_month = calendar.monthrange(today.year, today.month)[1]

    # Pull AWS cost data
    df = get_spend_timeseries_by_service(days=days_elapsed)

    if df.empty:
        print("⚠️ No AWS data returned (empty DataFrame)")
        return {
            "data": {
                "actual_spend": 0,
                "burn_rate": 0,
                "projected_spend": 0,
                "budget_limit": budget,
                "status": "no-data",
                "service_budgets": [],
            }
        }

    print(f"📊 AWS data received: {len(df)} rows")
    print(f"📊 Unique services: {df['service'].unique().tolist()}")

    # Overall MTD spend
    actual = df["cost"].sum()
    burn_rate = actual / days_elapsed
    projected = burn_rate * days_in_month

    # Status logic
    if projected > budget:
        status = "danger"
    elif projected > budget * 0.9:
        status = "warning"
    else:
        status = "good"

    # ------------------------------------------
    # 🚨 Slack Alerts (with deduplication)
    # ------------------------------------------
    alert_hash = hash_alert(status, actual, projected, budget)
    state = load_budget_state()

    # Only send if it's a NEW alert (status changed or values significantly different)
    # OR if force=true (for testing)
    should_send_alert = force or (state.get("last_alert_hash") != alert_hash)

    if should_send_alert:
        if status == "danger":
            send_slack_alert(
                "Budget Alert: Overspend",
                (
                    f"Projected spend (${projected:.2f}) exceeds your budget (${budget:.2f}).\n"
                    f"Current burn rate: ${burn_rate:.2f}/day\n"
                    f"MTD spend: ${actual:.2f}"
                ),
                emoji="🔴"
            )

        elif status == "warning":
            send_slack_alert(
                "Budget Risk Warning",
                (
                    f"Projected spend (${projected:.2f}) is close to the budget (${budget:.2f}).\n"
                    f"Current burn rate: ${burn_rate:.2f}/day"
                ),
                emoji="🟡"
            )

        # Save the new alert signature
        state["last_alert_hash"] = alert_hash
        state["last_alert_time"] = datetime.now(timezone.utc).isoformat()
        save_budget_state(state)

    # ------------------------------------------
    # 🔥 Build per-service budgets
    # ------------------------------------------
    service_budgets = build_service_budget_rows(df, days_elapsed, days_in_month)

    # ------------------------------------------
    # Final Response (frontend-ready)
    # ------------------------------------------
    return {
        "data": {
            "actual_spend": round(actual, 2),
            "burn_rate": round(burn_rate, 4),
            "projected_spend": round(projected, 2),
            "budget_limit": budget,
            "status": status,
            "days_elapsed": days_elapsed,
            "days_in_month": days_in_month,

            # NEW — what your frontend needs
            "service_budgets": service_budgets,
        }
    }
