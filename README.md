# ☁️ Cloud Cost AI

**AI-powered AWS Cost Analyzer & Anomaly Detector**  
_Built with FastAPI • Python • Streamlit • Slack Integration_

---

## 🌟 Overview

**Cloud Cost AI** monitors your AWS spending in real time — pulling Cost Explorer data, detecting anomalies with machine learning, and alerting your team via Slack before charges spiral out of control.

It’s designed for:
- 🧑‍💻 DevOps engineers and students experimenting with AWS free-tier  
- 🚀 Startups watching every cent of cloud usage  
- 🧠 Small teams needing AI-driven cost visibility without enterprise FinOps tools  

---

## 🧩 Features

✅ **Daily Cost Summary**
- Fetches AWS Cost Explorer data (`GetCostAndUsage`)
- Groups by day and service for clarity

✅ **AI-Powered Anomaly Detection**
- Uses `IsolationForest` to detect spikes and trend breaks
- Highlights which AWS services caused the cost deviation

✅ **Slack Alerts**
- Sends instant alerts when anomalies exceed threshold
- Customizable minimum-impact value

✅ **Interactive Dashboard**
- Built with Streamlit + Plotly
- Visualizes daily spend, service breakdown, and anomaly heatmaps

✅ **Hourly Auto-Notifier**
- Background Python job or Windows Task Scheduler
- De-duplicates repeated alerts using a local state file

---

## 🧠 Architecture

```text
FastAPI Backend (app/)
│
├── main.py                  → API entrypoint
│   ├── /spend/summary       → AWS Cost Explorer data (via boto3)
│   ├── /anomalies           → Detect anomalies (IsolationForest ML)
│   └── /anomalies/notify    → Push alerts to Slack
│
├── ml/
│   └── anomaly.py           → AI-based anomaly detection logic
│
├── services/
│   └── slack_notifier.py    → Slack webhook integration
│
└── jobs/
    └── hourly_notify.py     → Hourly scheduler to auto-send alerts
│
Streamlit Frontend (dashboard/)
│
├── app.py                   → Interactive dashboard (cost + anomalies)
│   ├── Fetches data from FastAPI
│   ├── Shows spend by service & anomaly heatmaps
│   └── Future tabs: Forecast, Slack trigger, Trends
│
.env                         → Local secrets (AWS + Slack)
.state/                      → Stores last alert signature (de-dupe)
⚙️ Setup Guide
1️⃣ Clone the repository
git clone https://github.com/<yourusername>/cloud-cost-ai.git
cd cloud-cost-ai

2️⃣ Create a virtual environment
python -m venv .venv312
.\.venv312\Scripts\activate

3️⃣ Install dependencies
pip install -r requirements.txt


Or manually:

pip install fastapi uvicorn boto3 pandas scikit-learn python-dotenv requests streamlit plotly

4️⃣ Configure environment

Create a .env file:

AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXXX/YYYY/ZZZZ


⚠️ Never commit .env to GitHub.
Add it to .gitignore immediately.

5️⃣ Run FastAPI backend
uvicorn app.main:app --reload --port 8080


Visit:

http://localhost:8080/docs

6️⃣ Run Streamlit dashboard
cd dashboard
streamlit run app.py


Open:

http://localhost:8501

7️⃣ (Optional) Enable hourly Slack alerts
python jobs/hourly_notify.py


Or schedule via Windows Task Scheduler to run hourly.

🧮 API Endpoints
Endpoint	Method	Description
/spend/summary?days=30	GET	Returns daily spend per AWS service
/anomalies?days=120&minimpact=0.1	GET	Detects cost anomalies
/anomalies/notify	GET	Sends top anomaly to Slack
💬 Example Slack Alert

🚨 AWS Cost Anomaly Detected
• Date: 2025-09-01
• Impact: $8.17
• EC2 – Other: +$1.2
• Tax: +$6.05
• Elastic Compute Cloud: +$0.9

🧱 Security Notes
Area	Risk	Fix
.env	Credentials leak if committed	Add to .gitignore
Slack Webhook	Anyone with URL can spam	Keep secret, rotate periodically
AWS IAM	Over-permissioned keys	Use least-privileged role (ce:GetCostAndUsage)
FastAPI	Public endpoints	Add API key middleware for prod
Streamlit	Open dashboard	Protect with Basic Auth / proxy
State file	Editable	Restrict permissions or use DB
Dependencies	Outdated	Run pip-audit or safety check
🧮 Example Workflow

User launches FastAPI backend

/spend/summary pulls AWS data (past N days)

/anomalies runs AI detection (IsolationForest)

/anomalies/notify pushes alert to Slack

Streamlit dashboard visualizes all results

Optional hourly job automates alert checks

🗺️ Roadmap
Version	Features
v1.0 (Now)	Core detection, Slack alerts, Streamlit dashboard
v2.0 (Next)	NAT Gateway & Elastic IP cost tracking
	AI forecast (Prophet/ARIMA)
	Live Slack trigger from dashboard
	Authentication for public deployment
🧑‍💻 Author

Iftekhar “Joy” Islam
💼 LinkedIn

🚀 DevOps • AI • Cloud Engineer
🌐 imjoy.me

⚖️ License

MIT License — free to use, modify, and share.

🤝 Contributing

Pull requests welcome!
Open an issue if you’d like to discuss ideas for:

Cost forecasting with AI

Kubernetes/Serverless deployment

Multi-cloud support (Azure, GCP)

🧾 Requirements (for reference)
fastapi
uvicorn
boto3
pandas
scikit-learn
python-dotenv
requests
streamlit
plotly

🎯 Example Output Preview

Slack alert example:

🚨 AWS Cost Anomaly Detected
Date: 2025-09-01
Impact: $8.17
EC2 – Other: +$1.2
Tax: +$6.05
Elastic Compute Cloud: +$0.9







requirements.txt             → Dependencies
README.md                    → Documentation
