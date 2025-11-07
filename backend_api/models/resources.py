from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

class ResourceCostItem(BaseModel):
    day: date = Field(..., example="2025-11-01", description="Billing date for this cost record")
    service: str = Field(..., example="Amazon EC2", description="AWS service name")
    resource_id: Optional[str] = Field(None, example="i-0a12b34cd56e", description="AWS resource ID")
    cost: float = Field(..., example=3.45, description="Daily cost in USD")
    usage_type: Optional[str] = Field(None, example="BoxUsage:t3.medium", description="AWS usage type or operation")
    region: Optional[str] = Field(None, example="ca-central-1", description="AWS region (if available)")

class ResourceCostResponse(BaseModel):
    data: List[ResourceCostItem] = Field(..., description="List of resource-level cost entries")
    message: Optional[str] = Field(None, example="No resource-level data found. Try again after 24h if just enabled.")
