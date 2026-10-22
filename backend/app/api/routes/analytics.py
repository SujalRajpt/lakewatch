import json
from typing import List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field
from pathlib import Path
import pyarrow.compute as pc
import pyarrow.parquet as pq
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, literal, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.reading import SensorReading

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/{lake_id}/aggregate")
async def get_agg(
    lake_id: str,
    db: AsyncSession = Depends(get_db),
):
    # Find the most recent completed five-minute window, excluding
    # the latest ten minutes to allow readings time to arrive.
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=10)

    interval = literal_column("INTERVAL '5 minutes'")
    origin = literal(datetime(2000, 1, 1, tzinfo=timezone.utc))

    bucket_query = select(func.date_bin(interval, literal(cutoff), origin))
    window_end = (await db.execute(bucket_query)).scalar_one()
    window_start = window_end - timedelta(minutes=5)

    exists_query = (
        select(func.count())
        .select_from(SensorReading)
        .where(
            SensorReading.lake_id == lake_id,
            SensorReading.event_timestamp >= window_start,
            SensorReading.event_timestamp < window_end,
        )
    )
    count = (await db.execute(exists_query)).scalar_one()

    if count == 0:
        raise HTTPException(
            status_code=404,
            detail=(
                "No readings available for the eligible five-minute "
                "window yet. Retry later."
            ),
        )

    bucket = func.date_bin(
        interval,
        SensorReading.event_timestamp,
        origin,
    ).label("window_start")

    query = (
        select(
            bucket,
            func.count().label("reading_count"),
            func.avg(SensorReading.temperature).label("avg_temperature"),
            func.min(SensorReading.temperature).label("min_temperature"),
            func.max(SensorReading.temperature).label("max_temperature"),
            func.avg(SensorReading.ph).label("avg_ph"),
            func.min(SensorReading.ph).label("min_ph"),
            func.max(SensorReading.ph).label("max_ph"),
            func.avg(SensorReading.dissolved_oxygen).label(
                "avg_dissolved_oxygen"
            ),
            func.avg(SensorReading.turbidity).label("avg_turbidity"),
            func.avg(SensorReading.conductivity).label("avg_conductivity"),
            func.avg(SensorReading.nitrate).label("avg_nitrate"),
        )
        .where(
            SensorReading.lake_id == lake_id,
            SensorReading.event_timestamp >= window_start,
            SensorReading.event_timestamp < window_end,
        )
        .group_by(bucket)
    )

    result = (await db.execute(query)).mappings().one()

    return {
        "lake_id": lake_id,
        "window_start": result["window_start"],
        "window_end": window_end,
        "reading_count": result["reading_count"],
        "temperature": {
            "avg": result["avg_temperature"],
            "min": result["min_temperature"],
            "max": result["max_temperature"],
        },
        "ph": {
            "avg": result["avg_ph"],
            "min": result["min_ph"],
            "max": result["max_ph"],
        },
        "dissolved_oxygen_avg": result["avg_dissolved_oxygen"],
        "turbidity_avg": result["avg_turbidity"],
        "conductivity_avg": result["avg_conductivity"],
        "nitrate_avg": result["avg_nitrate"],
    }



PROCESSED_PARQUET_PATH = Path(
    "/data-lake/processed/five_minute_summaries"
)


@router.get("/{lake_id}/parquet_read")
async def read_processed_parquet(
    lake_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
):
    """Read saved five-minute Spark summaries for a lake."""

    if not PROCESSED_PARQUET_PATH.is_dir():
        raise HTTPException(
            status_code=404,
            detail="Processed Parquet dataset not found.",
        )

    try:
        # Read the existing Spark output directory.
        table = pq.read_table(PROCESSED_PARQUET_PATH)

        required_columns = {
            "lake_id",
            "window_start",
            "window_end",
            "reading_count",
            "avg_temperature",
            "min_temperature",
            "max_temperature",
            "avg_ph",
            "min_ph",
            "max_ph",
            "avg_dissolved_oxygen",
            "avg_turbidity",
            "avg_conductivity",
            "avg_nitrate",
        }

        missing = required_columns - set(table.column_names)

        if missing:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Processed dataset is missing columns: "
                    f"{sorted(missing)}"
                ),
            )

        # Filter rows to the requested lake.
        lake_table = table.filter(
            pc.equal(table["lake_id"], lake_id)
        )

        if lake_table.num_rows == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No processed summaries found for {lake_id}.",
            )

        # Sort by window_start, newest first.
        indices = pc.sort_indices(
            lake_table,
            sort_keys=[("window_start", "descending")],
        )

        # Return only the requested number of records.
        indices = indices.slice(0, limit)   
        lake_table = lake_table.take(indices)

        # Convert Arrow values to JSON-compatible Python objects.
        records = lake_table.to_pylist()

        for record in records:
            for key, value in record.items():
                if hasattr(value, "isoformat"):
                    record[key] = value.isoformat()             

        return {
            "lake_id": lake_id,
            "returned": len(records),
            "records": records,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to read processed Parquet data.",
        ) from exc


class SparkQueryRequest(BaseModel):
    columns: List[str] = Field(min_items=1, max_items=6)
    days: int = Field(ge=1, le=3650)
    
  
ALLOWED_MEASUREMENTS = {
    "temperature",
    "ph",
    "dissolved_oxygen",
    "turbidity",
    "conductivity",
    "nitrate",
}

SPARK_RUNNER_URL = "http://host.docker.internal:9002/run-aggregation"


@router.post("/data-lake/spark-query")
def run_spark_query(request: SparkQueryRequest):
    """Run an on-demand Spark aggregation over raw Parquet data."""

    if len(set(request.columns)) != len(request.columns):
        raise HTTPException(
            status_code=422,
            detail="Duplicate measurement columns are not allowed.",
        )

    invalid_columns = set(request.columns) - ALLOWED_MEASUREMENTS
    if invalid_columns:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported columns: {sorted(invalid_columns)}",
        )

    payload = json.dumps({
        "columns": request.columns,
        "days": request.days,
    }).encode("utf-8")

    upstream_request = Request(
        SPARK_RUNNER_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(upstream_request, timeout=310) as response:
            return json.loads(response.read().decode("utf-8"))

    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise HTTPException(
            status_code=502,
            detail=f"Spark job runner returned an error: {detail}",
        ) from exc

    except (URLError, TimeoutError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not reach the Spark job runner or the request timed out.",
        ) from exc

    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail="Spark job runner returned invalid JSON.",
        ) from exc
