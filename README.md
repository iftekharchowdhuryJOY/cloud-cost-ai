# ☁️ Cloud Cost AI

AI-powered AWS cost analyzer and anomaly detector — built with FastAPI, Python, Streamlit, and lightweight ML (IsolationForest). Cloud Cost AI helps you catch unexpected spend, analyze daily service usage, and receive Slack alerts when costs spike.

---

## Overview

Cloud Cost AI monitors AWS Cost Explorer data, runs anomaly detection to find unusual spending patterns, and notifies your team via Slack. It's aimed at:

- DevOps engineers and students experimenting with the AWS free tier
- Startups keeping close watch on cloud spend
- Small teams that want AI-driven cost visibility without enterprise FinOps tools

---

## Features

- Daily cost summary: fetches Cost Explorer data (GetCostAndUsage), grouped by day and service  
- AI-powered anomaly detection: IsolationForest to surface spikes and trend breaks  
- Slack alerts: customizable threshold and minimum-impact filter  
- Interactive dashboard: Streamlit + Plotly for visualizations and drill-downs  
- Hourly notifier: background job or scheduler with simple de-duplication using local state

---

## Architecture

High-level layout:

```text
FastAPI Backend (app/)
│
├── main.py                  → API entrypoint
│   ├── /spend/summary       → Fetch AWS Cost Explorer (boto3)
│   ├── /anomalies           → Detect anomalies (IsolationForest)
│   └── /anomalies/notify    → Push alerts to Slack
│
├── ml/
│   └── anomaly.py           → Anomaly detection logic
│
├── services/
│   └── slack_notifier.py    → Slack webhook integration
│
└── jobs/
    └── hourly_notify.py     → Hourly scheduler to auto-send alerts

Streamlit Frontend (dashboard/)
├── app.py                   → Interactive dashboard that fetches the API
.env                         → Local secrets (AWS + Slack)
.state/                      → Stores last alert signature (for de-dup)
```

---

## Quick Start

Prerequisites:
- Python 3.9+
- An AWS account with Cost Explorer enabled
- Slack webhook (optional, for alerts)

1. Clone the repo
```bash
git clone https://github.com/iftekharchowdhuryJOY/cloud-cost-ai.git
cd cloud-cost-ai
```

2. Create & activate a virtual environment
(Windows example)
```bash
python -m venv .venv
.\.venv\Scripts\activate
```
(Unix/macOS example)
```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```
or manually:
```bash
pip install fastapi uvicorn boto3 pandas scikit-learn python-dotenv requests streamlit plotly
```

4. Configure environment variables

Create a `.env` file in the project root (do NOT commit this file):

```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXXX/YYYY/ZZZZ
```

5. Run the FastAPI backend
```bash
uvicorn app.main:app --reload --port 8080
```
Open API docs: http://localhost:8080/docs

6. Run the Streamlit dashboard
```bash
cd dashboard
streamlit run app.py
```
Open the dashboard: http://localhost:8501

7. (Optional) Start hourly notifier
```bash
python jobs/hourly_notify.py
```
Or schedule `jobs/hourly_notify.py` with your OS scheduler (cron, Task Scheduler, etc.).

---

## API Endpoints

| Endpoint | Method | Description |
|---------:|:------:|:------------|
| /spend/summary?days=30 | GET | Returns daily spend per AWS service |
| /anomalies?days=120&minimpact=0.1 | GET | Runs anomaly detection and returns anomalies |
| /anomalies/notify | POST | Sends top anomaly to Slack (or send payload) |

Notes:
- Adjust `days` and `minimpact` query parameters for different time windows and sensitivity.
- /anomalies/notify should be protected or used internally; consider adding API key middleware for production.

---

## Example Slack Alert

```
🚨 AWS Cost Anomaly Detected
Date: 2025-09-01
Impact: $8.17
• EC2 – Other: +$1.20
• Tax: +$6.05
• Elastic Compute Cloud: +$0.90
```

---

## Security & Best Practices

- .env — Never commit credentials; add `.env` to `.gitignore`.
- Slack webhook — Treat the URL as a secret; rotate periodically.
- AWS IAM — Use least-privileged credentials or an IAM role with permissions scoped to `ce:GetCostAndUsage`.
- FastAPI — Add authentication and rate limiting before exposing publicly.
- Streamlit — Protect dashboards behind auth or a proxy when deployed.
- State file — If using a local file for de-duplication, lock permissions or store signatures in a database for multi-instance setups.
- Dependencies — Regularly scan with pip-audit or safety.

---

## Example Workflow

1. FastAPI pulls Cost Explorer data via /spend/summary.
2. /anomalies runs IsolationForest over the recent window.
3. /anomalies/notify posts detected anomalies to Slack.
4. Streamlit dashboard visualizes spend + anomalies.
5. An hourly job can automate the previous steps and de-duplicate alerts.

---

## Roadmap

Planned items:
- v1.0: Core detection, Slack alerts, Streamlit dashboard (current)
- v2.0: NAT Gateway & Elastic IP cost tracking, AI forecasting (Prophet/ARIMA), live Slack trigger from dashboard, authentication for public deployments
- Future: Multi-cloud support (Azure, GCP), Kubernetes/serverless deployment

---

## Files of Interest

- requirements.txt — Python dependencies
- README.md — This documentation
- app/ — FastAPI backend source
- dashboard/ — Streamlit dashboard source
- jobs/ — Scheduled job helpers

---

## Contributing

Pull requests welcome. If you'd like to contribute:
- Open an issue to discuss major changes
- Fork the repo and make small, focused PRs
- Keep secrets out of commits

Suggestions for contributions:
- Cost forecasting models
- Better alerting rules and thresholds
- Secure deployment (auth, containerization)
- Multi-cloud support

---

## Author

Iftekhar “Joy” Islam  
DevOps • AI • Cloud Engineer — https://imjoy.me

---

## License

MIT License — free to use, modify, and share.