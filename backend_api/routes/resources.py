from fastapi import APIRouter, Query
from typing import Optional
from app.services.cost_explorer import get_resource_level_cost
from backend_api.models.resources import ResourceCostResponse
import pandas as pd

router = APIRouter(tags=["resources"])

@router.get("/costs/resources", response_model=ResourceCostResponse)
def resource_costs(
    start: str = Query(..., description="Start date YYYY-MM-DD"),
    end: str = Query(..., description="End date YYYY-MM-DD"),
    service: Optional[str] = Query(None, description="Filter by service"),
    region: Optional[str] = Query(None, description="Filter by region"),
):
    """
    Returns AWS cost data grouped by resource ID for the given date range.
    If resource-level data isn't yet enabled in Cost Explorer, the response will
    include a helpful message.
    """
    df = get_resource_level_cost(start, end, service, region)

    if isinstance(df, pd.DataFrame) and not df.empty:
        return {"data": df.to_dict(orient="records")}
    else:
        return {
            "data": [],
            "message": (
                "No resource-level cost data returned. "
                "If you just enabled resource-level data, AWS may need up to 24 hours "
                "to generate detailed results."
            ),
        }
