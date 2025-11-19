# Cloud Cost Optimizer AI — Coding Agent Guide

## Architecture Overview

**Cloud Cost Optimizer** is an AI-powered FinOps dashboard with three integrated layers:

```
AWS Cost Explorer (Boto3)
  ↓
FastAPI Backend (app/main.py + backend_api/main.py)
  ↓
ML Pipeline (IsolationForest + Prophet) + React Frontend + Slack Integration
```

- **`app/`**: FastAPI endpoints, ML models, jobs, and integrations
- **`backend_api/`**: Secondary API for React frontend with resource querying
- **`frontend/`**: React + Vite + Recharts dashboard (src/pages, src/components)

### Key Data Flow
1. **Cost Ingestion**: `app.services.cost_explorer.get_spend_timeseries_by_service()` pulls daily AWS spend per service via Boto3
2. **Anomaly Detection**: `app.ml.anomaly.detect_anomalies_isoforest()` flags abnormal spending (IsolationForest + trend breaks >50%)
3. **Forecasting**: `app.ml.forecast.train_and_forecast()` predicts 7-day spend using Facebook Prophet
4. **Alerting**: `app.services.slack_notifier.send_slack_alert()` posts to Slack webhook on anomalies/budget breaches
5. **UI**: React components fetch from `/api/costs`, `/api/resources`, and `/anomalies` endpoints

## Critical Conventions

### 1. Safe Mode Pattern
**All AWS-dependent functions check `USE_AWS` env var** to prevent failures in local/demo environments:
```python
USE_AWS = os.getenv("USE_AWS", "true").lower() == "true"
if not USE_AWS or client is None:
    return pd.DataFrame(columns=["day", "service", "cost"])  # empty fallback
```
When implementing new AWS-dependent features, **always include this guard**.

### 2. API Design: Two FastAPI Servers
- **`app.main`** (port 8080): Cost/anomaly queries, budget forecasting, Slack triggers
- **`backend_api.main`** (separate instance): React backend routes `/api/costs`, `/api/resources`

Both must be running. Start with:
```bash
uvicorn app.main:app --reload --port 8080
uvicorn backend_api.main:app --reload --port 8000  # separate terminal
```

### 3. Data Formats
- **Dates**: ISO format strings (YYYY-MM-DD) or Python `datetime.date` objects
- **DataFrames**: Columns consistently use `["day", "service", "cost"]` (or `["day", "service", "region"]` when region-grouped)
- **Costs**: Float values in USD, keyed as `"cost"` in records
- **API responses**: Always wrap results in `{"data": [...]}` or `{"results": [...]}`

### 4. ML Model Patterns
- **Anomaly scoring**: IsolationForest returns `decision_function` scores (lower = more anomalous, threshold = 0.10 quantile)
- **Trend breaks**: Flag when daily cost change >±50% vs 7-day rolling median
- **Forecast horizon**: Prophet model trained on aggregated daily spend, predicts 7 days ahead
- **Prophet columns**: Output DataFrame has `["ds", "yhat", "yhat_lower", "yhat_upper"]` — use `yhat` for point forecast

### 5. Slack Integration
```python
send_slack_alert(title, message, emoji="⚠️")
```
- Blocks if `SLACK_WEBHOOK_URL` env var is missing (no error raised, silent fallback)
- Use in jobs (`budget_guard.py`) and API background tasks
- Messages support Slack markdown syntax

## Essential Environment Variables
```bash
USE_AWS=true|false          # Toggle AWS API access (default: true)
AWS_REGION=ca-central-1     # AWS region (default: ca-central-1)
BUDGET_LIMIT_USD=10.00      # Budget threshold for alerts
SLACK_WEBHOOK_URL=...       # Slack webhook (required for alerts)
API_BASE=http://localhost:8080  # Backend URL for jobs
LOOKBACK_DAYS=90            # Historical days for forecast training
FORECAST_DAYS=7             # Forecast horizon
```

## Development Workflows

### Running Locally
```bash
# 1. Install deps + configure AWS credentials
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# 2. Set env vars
export USE_AWS=true USE_REGION=ca-central-1 SLACK_WEBHOOK_URL=...

# 3. Start both APIs (separate terminals)
uvicorn app.main:app --reload --port 8080
uvicorn backend_api.main:app --reload --port 8000

# 4. Start frontend (if modifying React)
cd frontend && npm run dev
```

### Testing Safely (No AWS Calls)
```bash
export USE_AWS=false
# All AWS endpoints return empty DataFrames — no credentials needed
```

### Manual Job Execution
```bash
python -m app.jobs.budget_guard  # Run budget forecast check once
# Or trigger via API: curl http://localhost:8080/budget/check
```

### Running in Docker
```bash
docker build -t cloud-cost-ai .
docker run -p 8080:8080 -p 8501:8501 -e SLACK_WEBHOOK_URL=... cloud-cost-ai
# Exposes: app.main on :8080, dashboard on :8501
```

## File Organization Principles

| Directory | Purpose | Key Pattern |
|-----------|---------|-------------|
| `app/ml/` | ML models | Input `pd.DataFrame`, return aggregated results or scored data |
| `app/services/` | AWS + external APIs | All functions check `USE_AWS` guard |
| `app/jobs/` | Scheduled tasks | Import from `app.services` + `app.ml`, call `send_slack_alert()` |
| `backend_api/routes/` | React-facing endpoints | Return `{"data": [records]}`, handle filtering params |
| `frontend/src/api/` | HTTP clients | Use `import.meta.env.VITE_API_URL`, wrap `axios` calls |
| `frontend/src/components/` | Recharts UI | Accept `data` prop (array of records), render with date/service/cost columns |

## Common Modifications

### Adding a New Cost Query Endpoint
1. Add function to `app/services/cost_explorer.py` (with `USE_AWS` guard)
2. Create route in `backend_api/routes/` that calls it
3. Export HTTP client from `frontend/src/api/`
4. Use in component with `useEffect(() => { getNewData() }, [])`

### Extending Anomaly Detection
- Edit `app/ml/anomaly.py` → `detect_anomalies_isoforest()` function
- Modify contamination rate, trend break threshold, or feature engineering
- Test via `GET /anomalies?days=120&minImpact=0` endpoint

### Adding a Slack Alert
- Call `send_slack_alert(title, message, emoji)` from jobs or API background task
- Ensure `SLACK_WEBHOOK_URL` env var is set
- Messages format: `f"{emoji} *{title}*\n{message}"` for Slack markdown

## Gotchas & Antipatterns

❌ **Don't**: Commit AWS credentials or Slack webhooks  
✅ **Do**: Use `.env` + `load_dotenv()` and pass via environment variables

❌ **Don't**: Hard-code dates or time windows in models  
✅ **Do**: Accept `days` parameter; use `datetime.now(timezone.utc)` for anchoring

❌ **Don't**: Assume `backend_api` and `app.main` run together  
✅ **Do**: Write jobs to fetch from `API_BASE` endpoint, not directly import models

❌ **Don't**: Return raw Prophet forecast (includes train data + future)  
✅ **Do**: Filter forecast to only future rows before API response

❌ **Don't**: Ignore empty DataFrames in `USE_AWS=false` mode  
✅ **Do**: Return consistent empty schema `["day", "service", "cost"]` for graceful degradation

## Tech Stack Reference
- **Backend**: FastAPI 0.115.4, Uvicorn
- **ML**: scikit-learn (IsolationForest), Prophet
- **Data**: pandas, numpy
- **Frontend**: React 19, Vite 7, Recharts, Tailwind CSS
- **AWS**: Boto3 (Cost Explorer API)
- **Notifications**: Slack webhooks (HTTP POST)
- **Config**: python-dotenv, Pydantic

---

*Last updated: 2025-11-18*
