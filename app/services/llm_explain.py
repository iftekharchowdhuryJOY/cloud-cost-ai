import os
import time
import json
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.services.cost_explorer import get_spend_timeseries_by_service
from app.db.database import SessionLocal
from app.db.service import BudgetService


# Env config
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")  # generic key for OpenAI or fallback
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
USE_LLM = os.getenv("USE_LLM", "true").lower() == "true" and bool(LLM_API_KEY or GROQ_API_KEY)


# Simple in-memory cache: key -> (expiry_ts, payload)
_CACHE: Dict[str, Any] = {}


def _cache_get(key: str) -> Optional[Dict[str, Any]]:
    row = _CACHE.get(key)
    if not row:
        return None
    exp, payload = row
    if time.time() > exp:
        _CACHE.pop(key, None)
        return None
    return payload


def _cache_set(key: str, payload: Dict[str, Any], ttl_sec: int = 1800) -> None:
    _CACHE[key] = (time.time() + ttl_sec, payload)


def _rolling_7d_median(series: pd.Series) -> float:
    last7 = series.tail(7)
    return float(np.median(last7)) if len(last7) else 0.0


def _moving_avg(series: pd.Series, window: int) -> float:
    if series.empty:
        return 0.0
    return float(series.rolling(window=window, min_periods=max(2, window//2)).mean().iloc[-1])


def _volatility(series: pd.Series) -> float:
    if len(series) < 2:
        return 0.0
    mean = float(series.tail(14).mean()) if len(series) >= 14 else float(series.mean())
    std = float(series.tail(14).std(ddof=0)) if len(series) >= 14 else float(series.std(ddof=0))
    return float(std / (mean + 1e-6)) if mean > 0 else 0.0


def _largest_1d_jump_window(s: pd.Series) -> Dict[str, Any]:
    if s.empty:
        return {"start": None, "end": None, "delta_usd": 0.0, "delta_pct": 0.0}
    s = s.reset_index(drop=True)
    # compute jump vs previous day
    prev = s.shift(1)
    delta = s - prev
    idx = int(delta.idxmax()) if delta.notna().any() else len(s) - 1
    today_cost = float(s.iloc[idx])
    # rolling 7d median based on prior 7 days window
    pre_7 = s.iloc[max(0, idx-7):idx]
    ref = float(np.median(pre_7)) if len(pre_7) else float(s.iloc[:idx].median() if idx > 0 else 0.0)
    delta_usd = float(today_cost - ref)
    delta_pct = float(delta_usd / (ref + 1e-6)) if ref > 0 else 0.0
    start = idx
    end = idx
    return {"start": start, "end": end, "delta_usd": delta_usd, "delta_pct": delta_pct}


def collect_spike_metrics(service: str, days: int = 30) -> Dict[str, Any]:
    df = get_spend_timeseries_by_service(days=days)
    df["day"] = pd.to_datetime(df["day"]).dt.date if not df.empty else df
    s_df = df[df["service"] == service].sort_values("day")
    if s_df.empty:
        return {"service": service, "error": "Service not found in window", "days": days}

    s = s_df["cost"].astype(float).reset_index(drop=True)
    today_cost = float(s.iloc[-1]) if len(s) else 0.0
    med7 = _rolling_7d_median(s)
    spike_ratio = float((today_cost - med7) / (med7 + 1e-6)) if med7 > 0 else 0.0
    accel_ratio = float((s.tail(7).mean()) / (s.iloc[:-7].tail(21).mean() + 1e-6)) if len(s) > 7 and s.iloc[:-7].tail(21).mean() > 0 else 1.0
    # anomaly density: count of days where cost > 1.5x 7d rolling median
    roll_med = s.rolling(window=7, min_periods=4).median()
    anom = (s > (roll_med * 1.5)) & roll_med.notna()
    anomaly_density = float(anom.mean()) if len(s) else 0.0
    volatility = _volatility(s)
    ma7 = _moving_avg(s, 7)
    ma30 = _moving_avg(s, 30)
    win = _largest_1d_jump_window(s)

    # budget pressure using existing budget table
    db = SessionLocal()
    try:
        b_obj = BudgetService.get_by_service(db, service)
        budget = float(b_obj.budget) if b_obj else None
    finally:
        db.close()

    # projected_30d using recent 14d avg
    ref_avg = float(s.tail(14).mean()) if len(s) >= 14 else float(s.mean())
    projected_30d = ref_avg * 30.0
    budget_pressure = (projected_30d / budget) if (budget and budget > 0) else None

    # spike dates
    start_idx = win["start"]
    end_idx = win["end"]
    days_list = list(s_df["day"].tolist())
    start_date = str(days_list[start_idx]) if start_idx is not None and start_idx < len(days_list) else None
    end_date = str(days_list[end_idx]) if end_idx is not None and end_idx < len(days_list) else None

    metrics = {
        "service": service,
        "days": days,
        "cost_today": round(today_cost, 2),
        "median_7d": round(med7, 2),
        "spike_ratio": round(spike_ratio, 3),
        "acceleration_ratio": round(accel_ratio, 3),
        "anomaly_density": round(anomaly_density, 3),
        "volatility": round(volatility, 3),
        "ma7": round(ma7, 2),
        "ma30": round(ma30, 2),
        "spike_window": {
            "start_date": start_date,
            "end_date": end_date,
            "cost_delta_usd": round(win["delta_usd"], 2),
            "cost_delta_pct": round(win["delta_pct"] * 100.0, 2),
        },
        "budget": budget,
        "projected_30d": round(projected_30d, 2),
        "budget_pressure": round(budget_pressure, 3) if budget_pressure is not None else None,
    }
    return metrics


def _build_prompt(metrics: Dict[str, Any], max_words: int = 120) -> Dict[str, Any]:
    schema_hint = {
        "summary": "string",
        "reason": "string",
        "drivers": ["string"],
        "recommendation": "string",
        "confidence": 0.0,
    }
    sys = (
        "You are a FinOps analyst. Use ONLY the provided metrics. "
        "Do not guess infrastructure details. "
        "Cite numbers exactly as given; do not invent new figures. "
        "Return a STRICT JSON object with keys: summary, reason, drivers, recommendation, confidence. "
        "Keep summary to ~{} words."
    ).format(max_words)

    user_lines = [
        f"service: {metrics['service']}",
        f"cost_today: {metrics['cost_today']}",
        f"median_7d: {metrics['median_7d']}",
        f"spike_ratio: {metrics['spike_ratio']}",
        f"acceleration_ratio: {metrics['acceleration_ratio']}",
        f"anomaly_density: {metrics['anomaly_density']}",
        f"volatility: {metrics['volatility']}",
        f"ma7: {metrics['ma7']}",
        f"ma30: {metrics['ma30']}",
        f"spike_window.cost_delta_usd: {metrics['spike_window']['cost_delta_usd']}",
        f"spike_window.cost_delta_pct: {metrics['spike_window']['cost_delta_pct']}",
        f"budget_pressure: {metrics.get('budget_pressure')}",
    ]

    prompt = {
        "system": sys,
        "user": "\n".join(user_lines) + "\nRespond ONLY with JSON.",
        "schema_hint": schema_hint,
    }
    return prompt


def _call_openai(prompt: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    import requests
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    # Use Responses API for 4.1 models
    body = {
        "model": LLM_MODEL,
        "input": [
            {
                "role": "system",
                "content": prompt["system"],
            },
            {
                "role": "user",
                "content": prompt["user"],
            },
        ],
        "max_output_tokens": 450,
    }
    url = "https://api.openai.com/v1/responses"
    try:
        r = requests.post(url, headers=headers, data=json.dumps(body), timeout=20)
        if r.status_code >= 400:
            return None
        data = r.json()
        # unified content
        text = None
        try:
            text = data["output"][0]["content"][0]["text"]
        except Exception:
            # fallback: some responses variants
            if isinstance(data.get("output"), dict):
                text = data["output"].get("text")
        if not text:
            return None
        return json.loads(text)
    except Exception:
        return None


def _call_groq(prompt: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Call Groq chat completion API and return parsed JSON or None."""
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY or LLM_API_KEY)
        messages = [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user"]},
        ]
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=450,
        )
        text = resp.choices[0].message["content"]
        return json.loads(text)
    except Exception:
        return None


def _fallback_explanation(metrics: Dict[str, Any], max_words: int = 120) -> Dict[str, Any]:
    # Deterministic narrative without LLM
    delta_pct = metrics["spike_window"]["cost_delta_pct"]
    acc = metrics["acceleration_ratio"]
    an = metrics["anomaly_density"]
    bp = metrics.get("budget_pressure")
    parts = [
        f"Spend increased {delta_pct:.1f}% vs the 7-day median.",
        f"Acceleration {acc:.2f}x and anomaly density {an:.2f} indicate a spike.",
    ]
    if bp is not None:
        if bp > 1.0:
            parts.append(f"Budget pressure is elevated ({bp:.2f}x), risk of breach.")
        elif bp >= 0.7:
            parts.append(f"Budget pressure at {bp:.2f}x, approaching limit.")
    summary = " ".join(parts)
    reason = "Spike defined as largest 1-day jump vs 7-day median in last week. Volatility {:.2f}.".format(metrics["volatility"]) 
    drivers = [
        f"7d MA {metrics['ma7']:.2f} vs 30d MA {metrics['ma30']:.2f}",
        f"Delta ${metrics['spike_window']['cost_delta_usd']:.2f} ({metrics['spike_window']['cost_delta_pct']:.1f}%)",
    ]
    reco = "Monitor next 3 days for persistence, verify recent workload changes, and set temporary cost caps if needed."
    return {
        "summary": summary,
        "reason": reason,
        "drivers": drivers,
        "recommendation": reco,
        "confidence": 0.7,
    }


def explain_spike(service: str, days: int = 30, detail: bool = False) -> Dict[str, Any]:
    metrics = collect_spike_metrics(service, days=days)
    if metrics.get("error"):
        return {"service": service, "error": metrics["error"]}

    # Cache key based on latest timestamp hash (day + last value)
    latest_hash = f"{metrics['spike_window']['end_date']}:{metrics['cost_today']}:{metrics['median_7d']}"
    cache_key = f"{service}:{days}:{latest_hash}:{'detail' if detail else 'concise'}"
    cached = _cache_get(cache_key)
    if cached:
        return {"service": service, "metrics": metrics, "explanation": cached}

    max_words = 280 if detail else 120
    if USE_LLM:
        prompt = _build_prompt(metrics, max_words=max_words)
        llm_json = None
        if LLM_PROVIDER == "groq":
            llm_json = _call_groq(prompt)
        else:
            llm_json = _call_openai(prompt)
        if llm_json and isinstance(llm_json, dict) and all(k in llm_json for k in ["summary", "reason", "drivers", "recommendation", "confidence"]):
            _cache_set(cache_key, llm_json)
            return {"service": service, "metrics": metrics, "explanation": llm_json}

    # Fallback deterministic
    fb = _fallback_explanation(metrics, max_words=max_words)
    _cache_set(cache_key, fb)
    return {"service": service, "metrics": metrics, "explanation": fb}
