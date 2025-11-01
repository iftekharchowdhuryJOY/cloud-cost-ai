import os, json, time, requests, pathlib
from datetime import datetime, timezone

PORT = os.environ.get("PORT", "8080")
DAYS = os.environ.get("ANOMALY_DAYS", "120")
MIN_IMPACT = os.environ.get("MIN_IMPACT", "0.1")  # dollars
URL = f"http://localhost:{PORT}/anomalies?days={DAYS}&minImpact={MIN_IMPACT}"

STATE_DIR = pathlib.Path(".state")
STATE_DIR.mkdir(exist_ok=True)
STATE_FILE = STATE_DIR / "last_alert.json"

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_day": None, "last_hash": None}

def save_state(s):
    STATE_FILE.write_text(json.dumps(s))

def hash_payload(item):
    # simple stable signature for de-dupe
    return json.dumps(
        {"day": item.get("day"), "impact_usd": item.get("impact_usd"),
         "top_services": item.get("top_services", [])},
        sort_keys=True
    )

def main():
    try:
        r = requests.get(URL, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print("Request failed:", e)
        return

    results = data.get("results", [])
    if not results:
        print(f"[{datetime.now(timezone.utc)}] No anomalies.")
        return

    latest = results[0]  # already sorted by impact desc in our API
    sig = hash_payload(latest)
    st = load_state()

    # Avoid spamming same alert repeatedly
    if st.get("last_hash") == sig:
        print(f"[{datetime.now(timezone.utc)}] Same anomaly as last time; skipping.")
        return

    # Call the notify endpoint to send Slack
    try:
        r2 = requests.get(
            f"http://localhost:{PORT}/anomalies/notify?days={DAYS}&minImpact={MIN_IMPACT}",
            timeout=20
        )
        r2.raise_for_status()
        print(f"[{datetime.now(timezone.utc)}] Alert sent:", r2.json())
        st["last_hash"] = sig
        st["last_day"] = latest.get("day")
        save_state(st)
    except Exception as e:
        print("Notify failed:", e)

if __name__ == "__main__":
    main()
