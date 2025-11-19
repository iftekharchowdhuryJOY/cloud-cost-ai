from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timezone
from app.services.cost_explorer import get_spend_timeseries_by_service

router = APIRouter(tags=["service-budgets"])

# TEMP STORAGE (Later → move to DB)
SERVICE_BUDGETS = {
    "AmazonEC2": 10,
    "AmazonS3": 5,
    "AWSLambda": 2,
    "AmazonCloudWatch": 3,
}

class BudgetUpdate(BaseModel):
    service: str
    budget: float


@router.get("/budget/services")
def get_service_budgets():
    return {"budgets": SERVICE_BUDGETS}


@router.post("/budget/services")
def update_budget(data: BudgetUpdate):
    SERVICE_BUDGETS[data.service] = data.budget
    return {"message": "updated", "service": data.service, "budget": data.budget}


@router.get("/budget/services/usage")
def service_usage():
    today = datetime.now(timezone.utc).date()
    df = get_spend_timeseries_by_service(days=30)

    if df.empty:
        return {"services": []}

    # Sum cost per service
    grouped = df.groupby("service")["cost"].sum().reset_index()

    results = []
    for _, row in grouped.iterrows():
        key = row["service"]
        actual = float(row["cost"])
        budget = SERVICE_BUDGETS.get(key, None)

        if budget:
            status = (
                "danger" if actual > budget
                else "warning" if actual > budget * 0.9
                else "good"
            )
        else:
            status = "no-budget"

        results.append({
            "service": key,
            "actual": actual,
            "budget": budget,
            "status": status
        })

    return {"services": results}
