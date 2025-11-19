from fastapi import APIRouter, Query
from app.services.anomaly_detector import detect_anomalies

router = APIRouter()

@router.get("/api/anomalies")
def anomalies(start: str, end: str, threshold: float = 1.3):
    """
    Detect anomalies in AWS spend.
    threshold: how much higher cost must be compared to baseline (1.3 = 30% increase)
    """
    data = detect_anomalies(start, end, threshold)
    return {"data": data}
