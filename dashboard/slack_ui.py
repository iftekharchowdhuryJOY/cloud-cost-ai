import requests
import streamlit as st

API_BASE = "http://localhost:8080"

def slack_trigger_tab():
    st.header("🚨 Manual Slack Alert")

    days = st.number_input("Days lookback", 7, 180, 120)
    minImpact = st.number_input("Min Impact ($)", 0.0, 50.0, 0.1, step=0.1)

    if st.button("Send Latest Anomaly to Slack"):
        try:
            url = f"{API_BASE}/anomalies/notify?days={days}&minImpact={minImpact}"
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                st.success("✅ Alert sent to Slack!")
                st.json(r.json())
            else:
                st.error(f"Slack call failed: {r.status_code}")
        except Exception as e:
            st.error(f"Error: {e}")
