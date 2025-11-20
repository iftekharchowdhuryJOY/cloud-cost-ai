from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.db.database import Base


class ServiceBudget(Base):
    """Service budget model for persistent storage."""
    __tablename__ = "service_budgets"

    id = Column(Integer, primary_key=True, index=True)
    service = Column(String, unique=True, index=True, nullable=False)
    budget = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "service": self.service,
            "budget": self.budget,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"

    id = Column(Integer, primary_key=True, index=True)
    service = Column(String, index=True, nullable=False)
    action = Column(String, nullable=False)  # 'accept' | 'dismiss'
    details = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "service": self.service,
            "action": self.action,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
