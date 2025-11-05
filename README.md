# ☁️ Cloud Cost Optimizer AI
**Real-time AWS Cost Insights + AI Forecast + Slack Control**  
Monitor AWS spending, detect anomalies, forecast future costs, and receive proactive alerts before your budget burns.

---

## 🌟 Overview

Cloud Cost Optimizer AI is an **AI-powered FinOps dashboard** that brings visibility, prediction, and automation to your AWS cloud costs.

It continuously analyzes AWS Cost Explorer data, detects **cost anomalies** using machine learning (Isolation Forest), and **forecasts upcoming spend** using Facebook Prophet.  
Slack integration ensures you get alerts instantly — before surprises hit your credit card.

---

## 🧠 Features

- ✅ **AWS Cost Visualization** — Real-time cost breakdown by service  
- ⚠️ **Anomaly Detection** — Detects sudden or abnormal cost spikes  
- 📈 **Forecasting (Prophet)** — Predicts upcoming AWS bills (next 7 days)  
- 💳 **Budget Tracking** — Shows cumulative spend, burn rate, and top services  
- 🔔 **Slack Alerts** — Sends automatic anomaly notifications  
- 🧩 **FastAPI Backend + Streamlit Dashboard** — Seamless and modular  
- 🤖 **AI Core** — Isolation Forest + Prophet for pattern learning and prediction

---

## 🏗️ Architecture

                    ┌────────────────────────────┐
                    │     AWS Cost Explorer      │
                    └────────────┬───────────────┘
                                 │
                                 ▼
                    ┌────────────────────────────┐
                    │        FastAPI API         │
                    │  /spend, /anomalies, /ml   │
                    └────────────┬───────────────┘
                                 │
                                 ▼
                    ┌────────────────────────────┐
                    │     ML Engine (AI Core)    │
                    │ IsolationForest + Prophet  │
                    └────────────┬───────────────┘
                                 │
                                 ▼
                    ┌────────────────────────────┐
                    │     Streamlit Dashboard    │
                    │  Spend | Anomalies | Slack │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌────────────────────────────┐
                    │   Slack Notifications Bot  │
                    └────────────────────────────┘

---

## 📊 Dashboard & Alerts Preview

Below are sample screenshots showing the dashboard and alerting experience. The Slack screenshot at the top gives an immediate sense of what alerts look like in-channel.

<p align="center">
  <img src="https://github.com/iftekharchowdhuryJOY/cloud-cost-ai/blob/main/docs/img/dashboard.png" width="90%" alt="Spend Overview">
  <br>
  <em>💵 Spend Overview — Real-time AWS spend by service</em>
</p>

<p align="center">
  <img src="https://github.com/iftekharchowdhuryJOY/cloud-cost-ai/blob/main/docs/img/anomalies.png" width="90%" alt="Anomaly Detection">
  <br>
  <em>⚠️ Anomaly Detection — AI-driven cost spikes by day/service</em>
</p>

<p align="center">
  <img src="https://github.com/iftekharchowdhuryJOY/cloud-cost-ai/blob/main/docs/img/aws_cost_forecast.png" width="90%" alt="Forecast">
  <br>
  <em>📈 Forecast — Prophet-based 7-day AWS spend prediction</em>
</p>

<p align="center">
  <img src="https://github.com/iftekharchowdhuryJOY/cloud-cost-ai/blob/main/docs/img/daily_burn.png" width="90%" alt="Daily burn">
  <br>
  <em>💳 Budget & Burn — Daily usage and top costly services</em>
</p>

<p align="center">
  <img src="https://github.com/iftekharchowdhuryJOY/cloud-cost-ai/blob/main/docs/img/slack_aleart.png" width="90%" alt="Slack integration screenshot">
  <br>
  <em>🔔 Slack Integration — One-click anomaly alerts</em>
</p>

<p align="center">
  <img src="https://github.com/iftekharchowdhuryJOY/cloud-cost-ai/blob/main/docs/img/slack_screenshot.png" width="90%" alt="Slack notification">
  <br>
  <em>🔔 Slack Notification</em>
</p>
---

## ⚙️ Setup Guide

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/iftekharchowdhuryJOY/cloud-cost-ai.git
cd cloud-cost-ai
python -m venv .venv
source .venv/bin/activate    # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2️⃣ AWS Credentials

Create or update `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = YOUR_KEY
aws_secret_access_key = YOUR_SECRET
region = ca-central-1
```

### 3️⃣ Environment Variables

Export your Slack webhook (example):
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/XXX/YYY/ZZZ"
```

### 4️⃣ Run the Services

Start FastAPI:
```bash
uvicorn app.main:app --reload --port 8080
```

Start the Streamlit dashboard:
```bash
streamlit run dashboard/app.py
```

Run scheduled job manually (budget guard example):
```bash
python -m app.jobs.budget_guard
```

Example output:
```
📊 Forecasted spend for 2025-11-02: $0.13
✅ Forecast $0.13 within budget ($10.00).
```

---

## 📁 Project Structure

Add this project layout to README to make the repo structure clear:

```
cloud-cost-optimizer/
├── app/
│   ├── actions/                # (optional) future automations
│   ├── jobs/                   # scheduled jobs
│   ├── ml/                     # ML modules (anomaly, forecast)
│   ├── services/               # slack notifier, helpers
│   └── main.py                 # FastAPI app
│
├── dashboard/
│   ├── app.py                  # Streamlit entry
│   ├── budget_ui.py            # Budget & burn tab
│   ├── forecast.py             # Forecast tab
│   └── slack_ui.py             # Slack trigger UI
│
├── docs/
│   └── img/
│       ├── anomalies.png
│       ├── aws_cost_forecast.png
│       ├── daily_burn.png
│       ├── dashboard.png
│       └── slack_aleart.png    # (kept filename as-is)
│
├── Dockerfile
├── README.md
└── requirements.txt
```

---

## 📢 Tech Stack

| Layer | Technology |
|-------|------------|
| Backend API | FastAPI |
| Frontend Dashboard | Streamlit |
| ML / Forecasting | scikit-learn, Prophet |
| Data Source | AWS Cost Explorer (Boto3) |
| Notifications | Slack Webhooks |
| Scheduler | APScheduler / Cron |
| Infra (Optional) | Docker, Terraform |

---

## 🔒 Security & Best Practices

- Never commit AWS keys or Slack webhooks to the repo. Use environment variables or secrets managers.
- Use IAM roles with least privilege for Cost Explorer access.
- Rotate credentials regularly.
- Limit Slack webhook exposure and rotate if leaked.

---


## 🧭 Workflow

- Data ingestion: scheduled jobs query AWS Cost Explorer
- ML pipeline: preprocess → train IsolationForest → detect anomalies → forecast with Prophet
- Alerting: Slack webhook triggered on anomalies or budget threshold breaches
- Dashboard: Streamlit reads API endpoints to display live data

---

## 🔔 Automation Example (Every Hour)
**If using cron or hosted service:
```bash
0 * * * * /path/to/.venv/bin/python /app/jobs/budget_guard.py
```
## 🧩 Future Roadmap (v2)

- AWS service-level drilldown
  - EC2 — cost by instance type, reservations, spot vs on-demand
  - S3 — storage classes, lifecycle costs, access patterns
  - NAT Gateway — per-hour and per-GB egress breakdown
- GPT-based cost explanation
  - Natural-language answers to “Why did my bill increase?”
  - Automated plain-English summaries and suggested remediations
- Multi-cloud support (GCP, Azure)
  - Unified ingestion and normalized metrics across providers
- Enhanced forecasting with seasonal trends
  - Improve Prophet models with seasonality, holidays, and confidence intervals
- Voice alert integration
  - Push critical alerts via voice (IVR or smart assistants) and escalation policies

## Contributing

Pull requests welcome. If you'd like to contribute:
- Open an issue to discuss major changes
- Fork the repo and make small, focused PRs
- Keep secrets out of commits

## Suggestions for contributions:
- Cost forecasting models
- Better alerting rules and thresholds
- Secure deployment (auth, containerization)
- Multi-cloud support

---

## Author

<b>JOY</b>
DevOps • AI • Cloud Engineer — https://imjoy.me

---

## 💬 License

MIT License © 2025 Iftekhar Joy

> **“AI should make DevOps proactive, not reactive.” — Joy**
