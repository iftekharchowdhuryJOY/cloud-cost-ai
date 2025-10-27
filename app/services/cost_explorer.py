import boto3
import pandas as pd
from datetime import datetime, timedelta, timezone
import os

AWS_REGION = os.environ.get("AWS_REGION", "ca-central-1")

def get_spend_timeseries_by_service(days: int = 30) -> pd.DataFrame:
    """
    Pull daily AWS costs per service using Cost Explorer API.
    """
    client = boto3.client("ce", region_name=AWS_REGION)
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days)

    response = client.get_cost_and_usage(
        TimePeriod={
            "Start": start.isoformat(),
            "End": end.isoformat()
        },
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