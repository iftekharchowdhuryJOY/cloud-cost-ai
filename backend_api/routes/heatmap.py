"""Risk heatmap API endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.cost_explorer import get_spend_timeseries_by_service
from app.services.risk_metrics import get_risk_heatmap_data
from app.db.database import get_db
from app.db.service import BudgetService

router = APIRouter(tags=["risk"])


@router.get("/budget/risk-heatmap")
def risk_heatmap(days: int = 30, db: Session = Depends(get_db)):
    """
    Get risk heatmap data for all services.
    
    Returns:
    {
        "heatmap": [
            {
                "service": "AmazonEC2",
                "actual_spend": 15.42,
                "budget": 20.0,
                "risk_level": "warning",
                "risk_score": 72,
                "utilization_pct": 77,
                "daily_burn": 0.514,
                "projected_spend": 15.42,
                "days_remaining": 10,
                "estimated_overspend": 0.0,
                "status_icon": "🟡",
            },
            ...
        ],
        "summary": {
            "total_services": 5,
            "danger_count": 1,
            "warning_count": 2,
            "good_count": 2,
            "no_budget_count": 0,
            "avg_risk_score": 45.2,
            "max_risk_score": 95,
        }
    }
    """
    
    # Get cost data
    df = get_spend_timeseries_by_service(days=days)
    
    # Get all budgets from database
    all_budgets = {b.service: b.budget for b in BudgetService.get_all(db)}
    
    # Calculate heatmap data
    heatmap_data = get_risk_heatmap_data(df, all_budgets)
    
    # Calculate summary statistics
    summary = {
        "total_services": len(heatmap_data),
        "danger_count": sum(1 for h in heatmap_data if h["risk_level"] == "danger"),
        "warning_count": sum(1 for h in heatmap_data if h["risk_level"] == "warning"),
        "good_count": sum(1 for h in heatmap_data if h["risk_level"] == "good"),
        "no_budget_count": sum(1 for h in heatmap_data if h["risk_level"] == "no-budget"),
        "avg_risk_score": round(sum(h["risk_score"] for h in heatmap_data) / len(heatmap_data), 1) if heatmap_data else 0,
        "max_risk_score": max((h["risk_score"] for h in heatmap_data), default=0),
    }
    
    return {
        "heatmap": heatmap_data,
        "summary": summary,
        "days_analyzed": days,
    }
