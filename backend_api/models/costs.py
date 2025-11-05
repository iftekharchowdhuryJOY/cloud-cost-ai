from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field

class CostItem(BaseModel):
    day: date = Field(..., description="Date of cost record")
    service: str = Field(..., description="AWS service name")
    cost: float = Field(..., description="Daily cost (USD)")
    region: Optional[str] = Field(None, description="AWS region")

class CostResponse(BaseModel):
    data: List[CostItem]
