from fastapi import APIRouter, Query
from typing import Optional
# Import your existing service code (no rewrite!)
from app.services.cost_explorer import get_spend_timeseries_by_service  # adjust name if needed

router = APIRouter(tags=["costs"])

@router.get("/costs")
def list_costs(
    start: str = Query(..., description="YYYY-MM-DD"),
    end: str = Query(..., description="YYYY-MM-DD"),
    service: Optional[str] = Query(None, description="Optional service filter"),
    region: Optional[str] = Query(None, description="Optional region filter"),
):
    """
    Returns service/resource-level cost for a date range.
    """
    # You likely already support params in your service;
    # if not, call the base function and filter here.
    data = get_spend_timeseries_by_service(start=start, end=end, service=service, region=region)
    return {"data": data}
