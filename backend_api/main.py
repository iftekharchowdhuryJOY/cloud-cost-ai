from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend_api.routes import costs, resources, anomalies, budget, service_budgets


app = FastAPI(title="Cloud Cost AI v2 API", version="0.1.0")

# CORS: allow your React/dev origins; adjust as needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to ["http://localhost:5173"] etc. later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Cloud Cost AI v2 API is running"}

# mount routes
app.include_router(costs.router, prefix="/api")
app.include_router(resources.router, prefix="/api")
app.include_router(anomalies.router, prefix="/api")
app.include_router(budget.router, prefix="/api")
app.include_router(service_budgets.router, prefix="/api")