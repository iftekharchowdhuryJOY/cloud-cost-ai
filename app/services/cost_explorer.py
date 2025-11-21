import boto3
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import logging
import time
import threading

# Load region and toggle
AWS_REGION = os.environ.get("AWS_REGION", "ca-central-1")
USE_AWS = os.getenv("USE_AWS", "true").lower() == "true"
# Optional TTL override for cost query caching (seconds). Set to 0 to disable.
COST_CACHE_TTL_SECONDS = int(os.getenv("COST_CACHE_TTL_SECONDS", "600"))

if USE_AWS:
    client = boto3.client("ce", region_name=AWS_REGION)
else:
    client = None
    logging.warning("⚠️ SAFE MODE: AWS Cost Explorer API disabled (USE_AWS=false)")


class _TTLCache:
    """Simple in-memory TTL cache for cost explorer responses.

    Rationale:
        Cost Explorer API is billed per request (~$0.01) and has throttling.
        UI refreshes or polling endpoints can easily duplicate identical queries.
        This lightweight cache reduces duplicate network calls and lowers cost.

    Behavior:
        - Key: tuple identifying the function + normalized parameters.
        - Value: (expires_epoch_seconds, pandas.DataFrame)
        - Thread-safe via a single Lock (sufficient for typical FastAPI workloads).
        - TTL controlled by env var COST_CACHE_TTL_SECONDS (default 600s).
        - Setting COST_CACHE_TTL_SECONDS=0 disables caching transparently.

    Notes:
        - Returned DataFrames are copied to avoid accidental mutation of cache.
        - Cache is in-process only (no cross-instance consistency).
        - Pruning is opportunistic during get/set operations (simple & cheap).
    """

    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()

    def _now(self) -> float:
        return time.time()

    def _prune(self):
        now = self._now()
        expired = [k for k, (exp, _) in self._store.items() if exp < now]
        for k in expired:
            self._store.pop(k, None)
        if expired:
            logging.debug(f"Cost cache pruned {len(expired)} expired entrie(s).")

    def get(self, key):
        if COST_CACHE_TTL_SECONDS <= 0:
            return None
        with self._lock:
            self._prune()
            entry = self._store.get(key)
            if not entry:
                return None
            exp, value = entry
            if exp < self._now():
                # Expired, remove & miss.
                self._store.pop(key, None)
                return None
            logging.debug(f"Cost cache HIT for key={key}")
            # Return a defensive copy.
            return value.copy()

    def set(self, key, value):
        if COST_CACHE_TTL_SECONDS <= 0:
            return value
        with self._lock:
            self._prune()
            expires = self._now() + COST_CACHE_TTL_SECONDS
            # Store a copy to avoid external mutation.
            self._store[key] = (expires, value.copy())
            logging.debug(f"Cost cache SET key={key} ttl={COST_CACHE_TTL_SECONDS}s")
        return value


_cache = _TTLCache()


def _cache_key(func_name: str, **kwargs):
    """Build a hashable cache key from function name and sorted kwargs."""
    # Normalize values that are DataFrames or complex types (not expected here).
    items = tuple(sorted(kwargs.items()))
    return (func_name, items)

def get_spend_timeseries_by_service(days: int = 30) -> pd.DataFrame:
    """Return daily AWS spend per service for the past N days.

    Caching:
        Results are cached in-memory keyed by (function, days) for TTL defined
        by COST_CACHE_TTL_SECONDS. Set COST_CACHE_TTL_SECONDS=0 to disable.

    Safe Mode:
        If USE_AWS=false, returns an empty DataFrame with schema
        ["day", "service", "cost"]. No caching needed but still performed
        (harmless) for interface consistency.
    """
    key = _cache_key("get_spend_timeseries_by_service", days=days)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    if not USE_AWS or client is None:
        logging.info("SAFE MODE active – returning empty dataframe instead of AWS data.")
        return _cache.set(key, pd.DataFrame(columns=["day", "service", "cost"]))

    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days)

    try:
        response = client.get_cost_and_usage(
            TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        data = []
        for day_block in response["ResultsByTime"]:
            day = day_block["TimePeriod"]["Start"]
            for g in day_block.get("Groups", []):
                service = g["Keys"][0]
                cost = float(g["Metrics"]["UnblendedCost"]["Amount"])
                data.append({"day": day, "service": service, "cost": cost})

        df = pd.DataFrame(data)
        if not df.empty:
            df["day"] = pd.to_datetime(df["day"]).dt.date
        return _cache.set(key, df)

    except Exception as e:
        logging.error(f"❌ Error fetching cost data: {e}")
        return _cache.set(key, pd.DataFrame(columns=["day", "service", "cost"]))

def get_cost_data(
    start: str = None,
    end: str = None,
    days: int = 30,
    service: str = None,
    region: str = None,
):
    """Flexible cost data query with optional service/region filtering.

    Parameters mirror existing behavior. Caching key considers the effective
    date range, service filter string, and region flag.

    Safe Mode:
        Returns empty DataFrame with columns ["day","service","cost","region"].
    """
    key = _cache_key(
        "get_cost_data",
        start=start,
        end=end,
        days=days,
        service=service,
        region=region,
    )
    cached = _cache.get(key)
    if cached is not None:
        return cached

    if not USE_AWS or client is None:
        logging.info("SAFE MODE active – returning empty dataframe instead of AWS data.")
        return _cache.set(key, pd.DataFrame(columns=["day", "service", "cost", "region"]))

    # Handle start & end vs days fallback
    if not start or not end:
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days)
    else:
        start_date = datetime.fromisoformat(start).date()
        end_date = datetime.fromisoformat(end).date()

    group_by = [{"Type": "DIMENSION", "Key": "SERVICE"}]
    if region:
        group_by.append({"Type": "DIMENSION", "Key": "REGION"})

    try:
        response = client.get_cost_and_usage(
            TimePeriod={"Start": start_date.isoformat(), "End": end_date.isoformat()},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            GroupBy=group_by,
        )

        data = []
        for day_block in response["ResultsByTime"]:
            day = day_block["TimePeriod"]["Start"]
            for g in day_block.get("Groups", []):
                service_name = g["Keys"][0]
                cost = float(g["Metrics"]["UnblendedCost"]["Amount"])
                record = {"day": day, "service": service_name, "cost": cost}
                if region and len(g["Keys"]) > 1:
                    record["region"] = g["Keys"][1]
                data.append(record)

        df = pd.DataFrame(data)
        if not df.empty:
            df["day"] = pd.to_datetime(df["day"]).dt.date
            if service:
                df = df[df["service"].str.contains(service, case=False, na=False)]
            if region:
                df = df[df.get("region", "").str.contains(region, case=False, na=False)]
        return _cache.set(key, df)

    except Exception as e:
        logging.error(f"❌ Error fetching cost data: {e}")
        return _cache.set(key, pd.DataFrame(columns=["day", "service", "cost", "region"]))

def get_resource_level_cost(start: str, end: str, service: str = None, region: str = None):
    """Resource-level daily cost (SERVICE + RESOURCE_ID) for a date range.

    Caching key incorporates full date range and service filter string.
    Region parameter is accepted for signature parity but not used in current
    GroupBy (Cost Explorer restricts combining too many dimensions). Ignored in
    cache key to avoid fragmentation while unused.
    """
    key = _cache_key(
        "get_resource_level_cost",
        start=start,
        end=end,
        service=service,
    )
    cached = _cache.get(key)
    if cached is not None:
        return cached

    if not USE_AWS or client is None:
        logging.info("SAFE MODE active – returning empty dataframe instead of AWS data.")
        return _cache.set(key, pd.DataFrame(columns=["day", "service", "resource_id", "cost"]))

    group_by = [
        {"Type": "DIMENSION", "Key": "SERVICE"},
        {"Type": "DIMENSION", "Key": "RESOURCE_ID"},
    ]

    try:
        response = client.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            GroupBy=group_by,
        )

        data = []
        for day_block in response["ResultsByTime"]:
            day = day_block["TimePeriod"]["Start"]
            for g in day_block.get("Groups", []):
                keys = g["Keys"]
                svc, resource_id = keys[:2]
                cost = float(g["Metrics"]["UnblendedCost"]["Amount"])
                data.append({"day": day, "service": svc, "resource_id": resource_id, "cost": cost})

        df = pd.DataFrame(data)
        if not df.empty:
            df["day"] = pd.to_datetime(df["day"]).dt.date
            if service:
                df = df[df["service"].str.contains(service, case=False, na=False)]
        return _cache.set(key, df)

    except Exception as e:
        logging.error(f"❌ Error fetching resource-level cost data: {e}")
        return _cache.set(key, pd.DataFrame(columns=["day", "service", "resource_id", "cost"]))
