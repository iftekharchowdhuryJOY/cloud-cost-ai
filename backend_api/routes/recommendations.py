from fastapi import APIRouter, Query, Body
from app.services.recommendations import generate_recommendations, explain_recommendation
from app.db.database import SessionLocal
from app.db.service import FeedbackService

router = APIRouter()

@router.get("/recommendations")
async def get_recommendations(days: int = Query(default=90, ge=7, le=365)):
    res = generate_recommendations(days=days)
    return res

@router.get("/recommendations/{service}/explain")
async def explain(service: str, days: int = Query(default=90, ge=7, le=365)):
    return explain_recommendation(service, days=days)


@router.post("/recommendations/{service}/accept")
async def accept_recommendation(service: str, details: str | None = Body(default=None)):
    db = SessionLocal()
    try:
        fb = FeedbackService.add_feedback(db, service=service, action="accept", details=details)
        return {"status": "ok", "feedback": fb.to_dict()}
    finally:
        db.close()


@router.post("/recommendations/{service}/dismiss")
async def dismiss_recommendation(service: str, details: str | None = Body(default=None)):
    db = SessionLocal()
    try:
        fb = FeedbackService.add_feedback(db, service=service, action="dismiss", details=details)
        return {"status": "ok", "feedback": fb.to_dict()}
    finally:
        db.close()
