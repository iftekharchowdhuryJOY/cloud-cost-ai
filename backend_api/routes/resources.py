from fastapi import APIRouter, Query
from typing import Optional
from app.services.cost_explorer import get_resource_level_cost
from pydantic import BaseModel, Field
from datetime import date
from typing import List

router = APIRouter(tags=["resources"])

class ResourceCostItem(BaseModel):
    day: date = Field(..., example="2025-11-01")
    service: str = Field(..., example="Amazon EC2")
    resource_id: str = Field(..., example="i-0abcd1234")
    region: str = Field(..., example="ca-central-1")
    cost: float = Field(..., example=3.45)

class ResourceCostResponse(BaseModel):
    data: List[ResourceCostItem]

@router.get("/costs/resources", response_model=ResourceCostResponse)
def resource_costs(
    start: str = Query(..., description="Start date YYYY-MM-DD"),
    end: str = Query(..., description="End date YYYY-MM-DD"),
    service: Optional[str] = Query(None, description="Filter by service"),
    region: Optional[str] = Query(None, description="Filter by region"),
):
    """
    Returns AWS cost data grouped by resource ID.
    """
    df = get_resource_level_cost(start, end, service, region)
    return {"data": df.to_dict(orient="records")}
