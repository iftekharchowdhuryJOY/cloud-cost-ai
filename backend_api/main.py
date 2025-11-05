from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend_api.routes import costs

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

# Tip: add more when ready
# from backend_api.routes import forecast, anomalies, budgets
# app.include_router(forecast.router, prefix="/api")
# app.include_router(anomalies.router, prefix="/api")
# app.include_router(budgets.router, prefix="/api")
