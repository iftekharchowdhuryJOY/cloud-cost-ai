from fastapi import APIRouter, Query, Body, Response
from fastapi.responses import StreamingResponse
from app.services.recommendations import generate_recommendations, explain_recommendation
from app.db.database import SessionLocal
from app.db.service import FeedbackService, AlertService, SettingsService
from app.db.models import RecommendationAlert, RecommendationFeedback, RecommendationRecovery
from sqlalchemy import func

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


@router.get("/recommendations/{service}/feedback")
async def feedback_history(service: str, limit: int = Query(default=5, ge=1, le=50)):
    """Return recent feedback actions for a recommendation service (default last 5)."""
    db = SessionLocal()
    try:
        rows = FeedbackService.recent_for_service(db, service=service, limit=limit)
        return {"data": [r.to_dict() for r in rows]}
    finally:
        db.close()


@router.get("/recommendations/alerts")
async def recent_alerts(days: int = Query(default=30, ge=1, le=365), limit: int = Query(default=100, ge=1, le=500)):
    """List recent high-priority recommendation alerts (not recovered events)."""
    from datetime import datetime, timezone, timedelta
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        rows = (
            db.query(RecommendationAlert)
            .filter(RecommendationAlert.created_at >= cutoff)
            .order_by(RecommendationAlert.created_at.desc())
            .limit(limit)
            .all()
        )
        return {"data": [r.to_dict() for r in rows], "summary": {"count": len(rows), "days": days}}
    finally:
        db.close()


@router.get("/recommendations/feedback/aggregate")
async def aggregate_feedback():
    """Aggregate feedback counts per service with last action timestamp/action."""
    db = SessionLocal()
    try:
        # Get counts per service/action
        counts_rows = (
            db.query(
                RecommendationFeedback.service,
                RecommendationFeedback.action,
                func.count(RecommendationFeedback.id).label("count"),
                func.max(RecommendationFeedback.created_at).label("last_time")
            )
            .group_by(RecommendationFeedback.service, RecommendationFeedback.action)
            .all()
        )

        # Structure data
        service_map = {}
        for r in counts_rows:
            svc = r[0]
            action = r[1]
            count = r[2]
            last_time = r[3]
            if svc not in service_map:
                service_map[svc] = {"service": svc, "accept_count": 0, "dismiss_count": 0, "last_feedback_action": None, "last_feedback_at": None}
            if action == "accept":
                service_map[svc]["accept_count"] += count
            elif action == "dismiss":
                service_map[svc]["dismiss_count"] += count
            # Update last feedback if newer
            cur_last = service_map[svc]["last_feedback_at"]
            if (not cur_last) or (last_time and last_time > cur_last):
                service_map[svc]["last_feedback_at"] = last_time
                service_map[svc]["last_feedback_action"] = action

        # Convert timestamps to iso
        results = []
        for v in service_map.values():
            v["last_feedback_at"] = v["last_feedback_at"].isoformat() if v["last_feedback_at"] else None
            results.append(v)
        return {"data": results, "summary": {"services": len(results)}}
    finally:
        db.close()


@router.get("/recommendations/recoveries")
async def recent_recoveries(limit: int = Query(default=50, ge=1, le=200)):
    db = SessionLocal()
    try:
        rows = (
            db.query(RecommendationRecovery)
            .order_by(RecommendationRecovery.created_at.desc())
            .limit(limit)
            .all()
        )
        return {"data": [r.to_dict() for r in rows], "summary": {"count": len(rows)}}
    finally:
        db.close()


@router.get("/recommendations/export")
async def export_recommendations(days: int = Query(default=90, ge=7, le=365)):
    import csv
    res = generate_recommendations(days=days)

    def row_iter():
        header = [
            "service","priority_score","base_priority_score","potential_savings_usd","budget",
            "projected_30d","acceleration_ratio","anomaly_density","volatility_ratio","feedback_action",
            "feedback_effect","alert_sent","alert_recovered","days_tracked"
        ]
        # Use csv module to ensure proper quoting
        import io
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(header)
        yield buf.getvalue()
        buf.seek(0); buf.truncate(0)
        for r in res.get("data", []):
            f = r.get("features", {})
            writer.writerow([
                r.get("service"),
                r.get("priority_score"),
                r.get("base_priority_score"),
                r.get("potential_savings_usd"),
                f.get("budget"),
                f.get("projected_30d"),
                f.get("acceleration_ratio"),
                f.get("anomaly_density"),
                f.get("volatility_ratio"),
                r.get("feedback_action"),
                r.get("feedback_effect"),
                r.get("alert_sent"),
                r.get("alert_recovered"),
                f.get("days_tracked"),
            ])
            yield buf.getvalue()
            buf.seek(0); buf.truncate(0)

    filename = f"recommendations_{days}d.csv"
    return StreamingResponse(
        row_iter(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/recommendations/summary")
async def recommendations_summary(days: int = Query(default=30, ge=1, le=365)):
    """Unified summary of alert, recovery, and feedback counts."""
    from datetime import datetime, timezone, timedelta
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        alert_count = db.query(RecommendationAlert).filter(RecommendationAlert.created_at >= cutoff).count()
        recovery_count = db.query(RecommendationRecovery).filter(RecommendationRecovery.created_at >= cutoff).count()
        feedback_counts = (
            db.query(RecommendationFeedback.action, func.count(RecommendationFeedback.id))
            .filter(RecommendationFeedback.created_at >= cutoff)
            .group_by(RecommendationFeedback.action)
            .all()
        )
        feedback_map = {a: c for a, c in feedback_counts}
        return {
            "days": days,
            "alerts": alert_count,
            "recoveries": recovery_count,
            "feedback": {
                "accept": feedback_map.get("accept", 0),
                "dismiss": feedback_map.get("dismiss", 0)
            }
        }
    finally:
        db.close()


@router.get("/recommendations/settings")
async def get_settings():
    db = SessionLocal()
    try:
        return {"data": SettingsService.get_all(db)}
    finally:
        db.close()


@router.patch("/recommendations/settings")
async def update_settings(payload: dict = Body(...)):
    allowed = set(SettingsService.DEFAULTS.keys())
    updates = {k: v for k, v in payload.items() if k in allowed}
    if not updates:
        return {"error": "No valid setting keys provided", "allowed_keys": list(allowed)}
    db = SessionLocal()
    try:
        data = SettingsService.upsert_many(db, updates)
        return {"data": data}
    finally:
        db.close()
