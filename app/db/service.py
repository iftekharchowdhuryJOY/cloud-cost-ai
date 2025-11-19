"""Database service for budget operations."""
from sqlalchemy.orm import Session
from app.db.models import ServiceBudget


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
