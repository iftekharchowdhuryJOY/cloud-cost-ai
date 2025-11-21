"""AI Chat API Routes.

Provides conversational FinOps assistance endpoints with service context
and metrics integration for cost spike analysis.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.services.llm_chat import generate_chat_reply

router = APIRouter(tags=["ai-chat"])


class ChatMessage(BaseModel):
    """Single chat message in conversation."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message text content")


class ChatPayload(BaseModel):
    """Request payload for chat endpoint."""
    messages: List[ChatMessage] = Field(..., description="Conversation history")
    service: Optional[str] = Field(None, description="AWS service name for metrics context")
    days: int = Field(30, ge=7, le=180, description="Historical days window for metrics")


class ChatResponse(BaseModel):
    """Chat response with updated messages and optional metrics."""
    messages: List[ChatMessage] = Field(..., description="Updated conversation including assistant reply")
    metrics: Dict[str, Any] | None = Field(None, description="Service metrics if service specified")


@router.post("/ai/chat", response_model=dict)
def ai_chat(payload: ChatPayload):
    """Generate AI chat reply with optional service context.
    
    Args:
        payload: Chat request with messages, optional service, and days window
        
    Returns:
        Dict with 'data' key containing messages and metrics
        
    Side effects:
        - Calls LLM API (Groq/OpenAI)
        - Fetches service metrics if service specified
    
    Example:
        POST /api/ai/chat
        {
          "messages": [{"role": "user", "content": "Why did costs spike?"}],
          "service": "Amazon Simple Storage Service",
          "days": 30
        }
    """
    result = generate_chat_reply(
        messages=[m.model_dump() for m in payload.messages],
        service=payload.service,
        days=payload.days,
    )
    return {"data": result}
