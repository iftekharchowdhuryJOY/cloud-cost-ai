from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

from app.services.llm_explain import explain_spike


router = APIRouter(tags=["ai"])


class ExplainResponse(BaseModel):
    service: str
    metrics: dict
    explanation: dict


@router.get("/ai/explain/{service}")
def ai_explain_service(service: str, days: int = Query(30, ge=7, le=180), detail: bool = False):
    """Explain a recent cost spike for a given service using metrics-only LLM prompt.

    - days: historical days for context (7-180)
    - detail: if true, generate a longer explanation
    """
    result = explain_spike(service, days=days, detail=detail)
    if result.get("error"):
        return {"error": result["error"], "service": service}
    # wrap in data as per conventions
    return {"data": result}
