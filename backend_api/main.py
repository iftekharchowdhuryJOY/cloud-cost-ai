from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend_api.routes import costs, resources, anomalies, budget, service_budgets, heatmap, service_trends
from app.db.database import init_db
from app.db.service import BudgetService
from app.db.database import SessionLocal


app = FastAPI(title="Cloud Cost AI v2 API", version="0.1.0")

# CORS: allow your React/dev origins; adjust as needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to ["http://localhost:5173"] etc. later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize database on startup
@app.on_event("startup")
def startup():
    """Create database tables and set default budgets on app startup."""
    init_db()
    
    # Set default budgets if they don't exist
    db = SessionLocal()
    try:
        defaults = {
            "AmazonEC2": 10,
            "Amazon Simple Storage Service": 5,
            "AWS Lambda": 2,
            "AmazonCloudWatch": 3,
        }
        BudgetService.bulk_set_defaults(db, defaults)
        print("✅ Database initialized with default budgets")
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Cloud Cost AI v2 API is running"}

# mount routes
app.include_router(costs.router, prefix="/api")
app.include_router(resources.router, prefix="/api")
app.include_router(anomalies.router, prefix="/api")
app.include_router(budget.router, prefix="/api")
app.include_router(service_budgets.router, prefix="/api")
app.include_router(heatmap.router, prefix="/api")
app.include_router(service_trends.router, prefix="/api")