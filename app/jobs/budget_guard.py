# app/jobs/budget_guard.py
import os, requests, pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from app.services.slack_notifier import send_slack_alert
from app.ml.forecast import train_and_forecast

load_dotenv()

API_BASE = os.getenv("API_BASE", "http://localhost:8080")
BUDGET_LIMIT = float(os.getenv("BUDGET_LIMIT_USD", 10.0))
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", 90))
FORECAST_DAYS = int(os.getenv("FORECAST_DAYS", 7))

def fetch_spend(days: int):
    """Fetch daily AWS spend from the backend API."""
    url = f"{API_BASE}/spend/summary?days={days}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json().get("results", [])
    return pd.DataFrame(data)

def check_budget_forecast():
    try:
        df = fetch_spend(LOOKBACK_DAYS)
        if df.empty:
            print("⚠️  No cost data available for forecast check.")
            return

        forecast = train_and_forecast(df, FORECAST_DAYS)
        tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)
        tomorrow_row = forecast[forecast["ds"].dt.date == tomorrow]

        if tomorrow_row.empty:
            print("⚠️  Forecast data not available for tomorrow.")
            return

        pred = float(tomorrow_row["yhat"].values[0])
        print(f"📊 Forecasted spend for {tomorrow}: ${pred:.2f}")

        if pred > BUDGET_LIMIT:
            msg = (
                f"⚠️ *Predicted Budget Breach*\n"
                f"Tomorrow’s AWS cost is forecasted at *${pred:.2f}*, "
                f"which exceeds your limit of *${BUDGET_LIMIT:.2f}*.\n"
                f"Consider reviewing high-impact services or pausing non-critical resources."
            )
            send_slack_alert(msg)
            print("✅ Slack alert sent.")
        else:
            print(f"✅ Forecast ${pred:.2f} within budget (${BUDGET_LIMIT:.2f}).")

    except Exception as e:
        print("❌ Error in budget guard:", e)

if __name__ == "__main__":
    check_budget_forecast()
