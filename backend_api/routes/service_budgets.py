from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.services.cost_explorer import get_spend_timeseries_by_service
from app.db.database import get_db
from app.db.service import BudgetService

router = APIRouter(tags=["service-budgets"])


class BudgetUpdate(BaseModel):
    service: str
    budget: float


class ServiceBudgetResponse(BaseModel):
    service: str
    actual: float
    budget: float | None
    status: str


@router.get("/budget/services")
def get_service_budgets(db: Session = Depends(get_db)):
    """Get all service budgets from database."""
    budgets = BudgetService.get_all(db)
    budget_dict = {b.service: b.budget for b in budgets}
    return {"budgets": budget_dict}


@router.post("/budget/services")
def update_budget(data: BudgetUpdate, db: Session = Depends(get_db)):
    """Update or create a service budget."""
    budget = BudgetService.update(db, data.service, data.budget)
    return {
        "message": "updated",
        "service": budget.service,
        "budget": budget.budget,
        "updated_at": budget.updated_at.isoformat() if budget.updated_at else None,
    }


@router.get("/budget/services/usage")
def service_usage(db: Session = Depends(get_db)):
    """Get usage vs budget for all services."""
    df = get_spend_timeseries_by_service(days=30)

    if df.empty:
        return {"services": []}

    # Sum cost per service
    grouped = df.groupby("service")["cost"].sum().reset_index()
    
    # Get all budgets from database
    all_budgets = {b.service: b for b in BudgetService.get_all(db)}

    results = []
    for _, row in grouped.iterrows():
        service_name = row["service"]
        actual = float(row["cost"])
        
        # Get budget from database, or None if not set
        budget_obj = all_budgets.get(service_name)
        budget_val = budget_obj.budget if budget_obj else None

        # Determine status
        if budget_val:
            status = (
                "danger" if actual > budget_val
                else "warning" if actual > budget_val * 0.9
                else "good"
            )
        else:
            status = "no-budget"

        results.append({
            "service": service_name,
            "actual": actual,
            "budget": budget_val,
            "status": status,
        })

    return {"services": results}
