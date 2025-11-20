"""Database service for budget operations."""
from sqlalchemy.orm import Session
from app.db.models import ServiceBudget, RecommendationFeedback, RecommendationAlert, RecommendationRecovery, RecommendationSetting


class BudgetService:
    """CRUD operations for service budgets."""

    @staticmethod
    def get_or_create(db: Session, service: str) -> ServiceBudget:
        """Get budget by service name, or create if not exists."""
        budget = db.query(ServiceBudget).filter(ServiceBudget.service == service).first()
        if not budget:
            budget = ServiceBudget(service=service, budget=0.0)
            db.add(budget)
            db.commit()
            db.refresh(budget)
        return budget

    @staticmethod
    def get_all(db: Session) -> list:
        """Get all service budgets."""
        return db.query(ServiceBudget).all()

    @staticmethod
    def get_by_service(db: Session, service: str) -> ServiceBudget:
        """Get budget by service name."""
        return db.query(ServiceBudget).filter(ServiceBudget.service == service).first()

    @staticmethod
    def update(db: Session, service: str, budget: float) -> ServiceBudget:
        """Update budget for a service. Creates if not exists."""
        existing = db.query(ServiceBudget).filter(ServiceBudget.service == service).first()
        
        if existing:
            existing.budget = budget
        else:
            existing = ServiceBudget(service=service, budget=budget)
            db.add(existing)
        
        db.commit()
        db.refresh(existing)
        return existing

    @staticmethod
    def delete(db: Session, service: str) -> bool:
        """Delete budget for a service."""
        budget = db.query(ServiceBudget).filter(ServiceBudget.service == service).first()
        if budget:
            db.delete(budget)
            db.commit()
            return True
        return False

    @staticmethod
    def bulk_set_defaults(db: Session, defaults: dict) -> None:
        """Bulk insert default budgets if they don't exist."""
        for service, budget in defaults.items():
            existing = db.query(ServiceBudget).filter(ServiceBudget.service == service).first()
            if not existing:
                db.add(ServiceBudget(service=service, budget=budget))
        db.commit()


class FeedbackService:
    """CRUD operations for recommendation feedback (accept/dismiss)."""

    @staticmethod
    def add_feedback(db: Session, service: str, action: str, details: str | None = None) -> RecommendationFeedback:
        fb = RecommendationFeedback(service=service, action=action, details=details)
        db.add(fb)
        db.commit()
        db.refresh(fb)
        return fb

    @staticmethod
    def recent_for_service(db: Session, service: str, limit: int = 10) -> list[RecommendationFeedback]:
        return (
            db.query(RecommendationFeedback)
            .filter(RecommendationFeedback.service == service)
            .order_by(RecommendationFeedback.created_at.desc())
            .limit(limit)
            .all()
        )


class AlertService:
    """Operations for recommendation alert persistence."""

    @staticmethod
    def record_alert(db: Session, service: str, priority_score: int, base_priority_score: int | None, feedback_action: str | None):
        alert = RecommendationAlert(
            service=service,
            priority_score=priority_score,
            base_priority_score=base_priority_score,
            feedback_action=feedback_action,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def has_recent_alert(db: Session, service: str, cooldown_days: int) -> bool:
        from datetime import datetime, timezone, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=cooldown_days)
        existing = (
            db.query(RecommendationAlert)
            .filter(RecommendationAlert.service == service, RecommendationAlert.created_at >= cutoff)
            .order_by(RecommendationAlert.created_at.desc())
            .first()
        )
        return existing is not None


class RecoveryService:
    """Persistence for recommendation recovery events."""

    @staticmethod
    def record_recovery(db: Session, service: str, previous_priority: int | None, recovery_priority: int, days_since_alert: int | None):
        rec = RecommendationRecovery(
            service=service,
            previous_priority=previous_priority,
            recovery_priority=recovery_priority,
            days_since_alert=days_since_alert,
        )


class SettingsService:
    """CRUD operations for recommendation settings."""

    DEFAULTS = {
        "RECOMMENDATION_ALERT_THRESHOLD": "70",
        "RECOMMENDATION_ALERT_COOLDOWN_DAYS": "7",
        "RECOMMENDATION_RECOVERY_DAYS": "3",
        "FEEDBACK_DISMISS_COOLDOWN_DAYS": "14",
        "FEEDBACK_ACCEPT_BOOST": "15",
        "FEEDBACK_DISMISS_PENALTY_FACTOR": "0.4",
    }

    @staticmethod
    def get_all(db: Session) -> dict:
        rows = db.query(RecommendationSetting).all()
        data = {r.key: r.value for r in rows}
        # Fill defaults if missing
        for k, v in SettingsService.DEFAULTS.items():
            if k not in data:
                data[k] = v
        return data

    @staticmethod
    def upsert_many(db: Session, updates: dict) -> dict:
        for k, v in updates.items():
            row = db.query(RecommendationSetting).filter(RecommendationSetting.key == k).first()
            if row:
                row.value = str(v)
            else:
                row = RecommendationSetting(key=k, value=str(v))
                db.add(row)
        db.commit()
        return SettingsService.get_all(db)
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec

    @staticmethod
    def recent(db: Session, limit: int = 50):
        return (
            db.query(RecommendationRecovery)
            .order_by(RecommendationRecovery.created_at.desc())
            .limit(limit)
            .all()
        )
