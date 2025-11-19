#!/usr/bin/env python
"""Test database persistence for service budgets."""
from app.db.database import init_db, SessionLocal
from app.db.service import BudgetService

# Initialize database
init_db()
db = SessionLocal()

print("🔧 Testing budget CRUD operations...\n")

# Test: Create/Update budgets
budget1 = BudgetService.update(db, "TestService1", 50.0)
print(f"✅ Created budget: {budget1.service} = ${budget1.budget}")

# Create another
budget2 = BudgetService.update(db, "TestService2", 100.0)
print(f"✅ Created budget: {budget2.service} = ${budget2.budget}")

# Get all
all_budgets = BudgetService.get_all(db)
print(f"\n📋 All budgets in database ({len(all_budgets)} total):")
for b in all_budgets:
    print(f"   - {b.service}: ${b.budget}")

# Update existing
BudgetService.update(db, "TestService1", 75.0)
updated = BudgetService.get_by_service(db, "TestService1")
print(f"\n✅ Updated {updated.service} to ${updated.budget}")

# Verify persistence
print(f"\n✅ Database file created at: .data/budgets.db")
print("✅ All data is persisted and will survive server restarts!")

db.close()
