import os, requests

def send_slack_alert(title: str, message: str, emoji: str = "⚠️"):
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        print("⚠️  No Slack webhook configured.")
        return False

    payload = {
        "text": f"{emoji} *{title}*\n{message}"
    }

    try:
        r = requests.post(webhook, json=payload, timeout=10)
        r.raise_for_status()
        print(f"✅ Slack alert sent: {title}")
        return True
    except Exception as e:
        print(f"❌ Slack alert failed: {e}")
        return False
