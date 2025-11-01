import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta

API_BASE = os.getenv("API_BASE", "http://localhost:8080")

@st.cache_data(ttl=300)
def fetch_summary(days: int):
    r = requests.get(f"{API_BASE}/spend/summary?days={days}", timeout=20)
    r.raise_for_status()
    data = r.json().get("results", [])
    df = pd.DataFrame(data)
    if df.empty:
        return df
    df["day"] = pd.to_datetime(df["day"])
    return df.sort_values("day")

def _month_bounds(anchor_date: pd.Timestamp):
    start = anchor_date.replace(day=1)
    end = (start + relativedelta(months=1)) - pd.Timedelta(days=1)
    return start, end

def _current_month(df: pd.DataFrame):
    if df.empty: 
        return df
    last_day = df["day"].max()
    start, end = _month_bounds(last_day)
    return df[(df["day"] >= start) & (df["day"] <= end)], start, end

def _cumulative_monthly(daily_df: pd.DataFrame):
    # daily_df has columns: day, cost (summed already)
    daily = daily_df.groupby("day", as_index=False)["cost"].sum().sort_values("day")
    daily["cum_cost"] = daily["cost"].cumsum()
    return daily

def _remaining_budget_gauge(spend_so_far: float, budget_limit: float):
    remaining = max(budget_limit - spend_so_far, 0)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=max(remaining, 0.0),
        number={'prefix': "$", 'valueformat': ".2f"},
        title={'text': "Remaining Budget (This Month)"},
        gauge={
            'axis': {'range': [0, max(budget_limit, 1.0)]},
            'bar': {'thickness': 0.35},
            'steps': [
                {'range': [0, budget_limit*0.5], 'color': "#ffdddd"},
                {'range': [budget_limit*0.5, budget_limit*0.85], 'color': "#fff1cc"},
                {'range': [budget_limit*0.85, budget_limit], 'color': "#e6ffe6"},
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': remaining
            }
        }
    ))
    fig.update_layout(margin=dict(l=10, r=10, t=60, b=10))
    return fig

def budget_tab():
    st.header("💳 Budget & Burn Analytics")

    col_top = st.columns(3)
    days_hist = col_top[0].number_input("History window (days)", 30, 180, 90)
    # default budget can be read from env (if set), else 10
    default_budget = float(os.getenv("BUDGET_LIMIT_USD", 10))
    monthly_budget = col_top[1].number_input("Monthly budget ($)", 1.0, 10000.0, default_budget, step=1.0)
    show_services = col_top[2].checkbox("Show top services table", value=True)

    df = fetch_summary(days_hist)
    if df.empty:
        st.warning("No cost data available.")
        return

    # Current month slice
    cur_month_df, month_start, month_end = _current_month(df)
    st.caption(f"Month window: **{month_start.date()} → {month_end.date()}**")

    # Cumulative view for current month
    daily_cur = cur_month_df.groupby("day", as_index=False)["cost"].sum().sort_values("day")
    cum_cur = _cumulative_monthly(daily_cur)

    spend_so_far = float(cum_cur["cum_cost"].iloc[-1]) if not cum_cur.empty else 0.0
    days_elapsed = (cum_cur["day"].max() - cum_cur["day"].min()).days + 1 if not cum_cur.empty else 0
    daily_avg = (spend_so_far / days_elapsed) if days_elapsed else 0.0

    # Top KPI row
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Spend so far (month)", f"${spend_so_far:.2f}")
    k2.metric("Monthly budget", f"${monthly_budget:.2f}")
    k3.metric("Daily burn (avg)", f"${daily_avg:.2f}/day")
    k4.metric("Remaining", f"${max(monthly_budget-spend_so_far, 0):.2f}")

    # Row: Gauge + Cumulative plot
    gcol, pcol = st.columns([1,2], gap="large")

    with gcol:
        fig_g = _remaining_budget_gauge(spend_so_far, monthly_budget)
        st.plotly_chart(fig_g, use_container_width=True)

    with pcol:
        # Cumulative spend vs budget line
        fig = px.line(cum_cur, x="day", y="cum_cost", title="Cumulative Spend vs Budget (This Month)")
        # Add budget reference as a flat line up to last day shown
        if not cum_cur.empty:
            fig.add_scatter(x=cum_cur["day"], y=[monthly_budget]*len(cum_cur), mode="lines",
                            name="Budget", line=dict(dash="dash"))
        fig.update_layout(xaxis_title="Date", yaxis_title="Cumulative Cost ($)")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📊 Daily Burn Rate")
    # Show daily cost last N days (not only current month) for trend context
    daily_hist = df.groupby("day", as_index=False)["cost"].sum().sort_values("day")
    fig_burn = px.bar(daily_hist, x="day", y="cost", title=f"Daily Burn (Last {days_hist} Days)")
    fig_burn.update_layout(xaxis_title="Date", yaxis_title="Daily Cost ($)")
    st.plotly_chart(fig_burn, use_container_width=True)

    if show_services:
        st.subheader("🧩 Top Services This Month")
        svc_month = cur_month_df.groupby(["service"], as_index=False)["cost"].sum().sort_values("cost", ascending=False)
        st.dataframe(svc_month, use_container_width=True)
