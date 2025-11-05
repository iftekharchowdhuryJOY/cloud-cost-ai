from fastapi import APIRouter, Query
from typing import Optional
from app.services.cost_explorer import get_cost_data

router = APIRouter(tags=["costs"])

@router.get("/costs")
def list_costs(
    start: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    days: int = Query(30, description="If start & end not provided, fetch last N days"),
    service: Optional[str] = Query(None, description="Filter by AWS service name"),
    region: Optional[str] = Query(None, description="Filter by region"),
):
    """
    Returns daily AWS cost per service for a date range or last N days.
    """
    df = get_cost_data(start, end, days, service, region)
    return {"data": df.to_dict(orient="records")}
