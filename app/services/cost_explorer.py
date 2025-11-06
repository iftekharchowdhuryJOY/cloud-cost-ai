import boto3
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import logging

# Load region and toggle
AWS_REGION = os.environ.get("AWS_REGION", "ca-central-1")
USE_AWS = os.getenv("USE_AWS", "true").lower() == "true"

if USE_AWS:
    client = boto3.client("ce", region_name=AWS_REGION)
else:
    client = None
    logging.warning("⚠️ SAFE MODE: AWS Cost Explorer API disabled (USE_AWS=false)")

def get_spend_timeseries_by_service(days: int = 30) -> pd.DataFrame:
    """
    Pull daily AWS costs per service using Cost Explorer API.
    If USE_AWS is false, return an empty DataFrame.
    """
    if not USE_AWS or client is None:
        logging.info("SAFE MODE active – returning empty dataframe instead of AWS data.")
        return pd.DataFrame(columns=["day", "service", "cost"])

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
        return df

    except Exception as e:
        logging.error(f"❌ Error fetching cost data: {e}")
        return pd.DataFrame(columns=["day", "service", "cost"])

def get_cost_data(
    start: str = None,
    end: str = None,
    days: int = 30,
    service: str = None,
    region: str = None,
):
    """
    Fetch AWS cost data between start & end or for the last N days.
    Optionally filter by service or region.
    """
    if not USE_AWS or client is None:
        logging.info("SAFE MODE active – returning empty dataframe instead of AWS data.")
        return pd.DataFrame(columns=["day", "service", "cost", "region"])

    # Handle start & end vs days fallback
    if not start or not end:
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days)
    else:
        start_date = datetime.fromisoformat(start).date()
        end_date = datetime.fromisoformat(end).date()

    # Base GroupBy
    group_by = [{"Type": "DIMENSION", "Key": "SERVICE"}]

    # If region filter requested, add it to GroupBy
    if region:
        group_by.append({"Type": "DIMENSION", "Key": "REGION"})

    try:
        response = client.get_cost_and_usage(
            TimePeriod={
                "Start": start_date.isoformat(),
                "End": end_date.isoformat(),
            },
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

                record = {
                    "day": day,
                    "service": service_name,
                    "cost": cost,
                }

                # If region was grouped, handle multiple keys
                if region and len(g["Keys"]) > 1:
                    record["region"] = g["Keys"][1]

                data.append(record)

        df = pd.DataFrame(data)

        # Optional post-filter by service or region if user passed filter
        if not df.empty:
            df["day"] = pd.to_datetime(df["day"]).dt.date
            if service:
                df = df[df["service"].str.contains(service, case=False, na=False)]
            if region:
                df = df[df.get("region", "").str.contains(region, case=False, na=False)]

        return df

    except Exception as e:
        logging.error(f"❌ Error fetching cost data: {e}")
        return pd.DataFrame(columns=["day", "service", "cost", "region"])

def get_resource_level_cost(start: str, end: str, service: str = None, region: str = None):
    """
    Fetch AWS cost data grouped by resource ID for a specific date range.
    Optionally filter by service or region.
    """
    if not USE_AWS or client is None:
        logging.info("SAFE MODE active – returning empty dataframe instead of AWS data.")
        return pd.DataFrame(columns=["day", "service", "resource_id", "cost"])

    # ✅ Only two allowed: SERVICE and RESOURCE_ID
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
                data.append({
                    "day": day,
                    "service": svc,
                    "resource_id": resource_id,
                    "cost": cost
                })

        df = pd.DataFrame(data)

        # Optional post-filtering
        if not df.empty:
            df["day"] = pd.to_datetime(df["day"]).dt.date
            if service:
                df = df[df["service"].str.contains(service, case=False, na=False)]

        return df

    except Exception as e:
        logging.error(f"❌ Error fetching resource-level cost data: {e}")
        return pd.DataFrame(columns=["day", "service", "resource_id", "cost"])
