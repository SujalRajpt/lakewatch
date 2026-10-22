
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


RAW_DIR = Path("/workspace/data-lake/raw")
OUTPUT_DIR = Path("/workspace/data-lake/processed/on_demand")

ALLOWED_COLUMNS = {
    "temperature",
    "ph",
    "dissolved_oxygen",
    "turbidity",
    "conductivity",
    "nitrate",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, required=True)
    parser.add_argument("--columns", required=True)
    args = parser.parse_args()

    columns = list(dict.fromkeys(args.columns.split(",")))

    if not 1 <= args.days <= 3650:
        raise ValueError("days must be between 1 and 3650")

    if not columns or any(
        column not in ALLOWED_COLUMNS for column in columns
    ):
        raise ValueError("One or more requested columns are not allowed")

    # Each raw file is a full snapshot. Read only the newest one.
    snapshots = sorted(RAW_DIR.glob("sensor_readings_*.parquet"))

    if not snapshots:
        raise FileNotFoundError(f"No raw Parquet snapshots found in {RAW_DIR}")

    input_path = snapshots[-1]

    # Parquet event timestamps are naive UTC in our current dataset.
    end_time = datetime.now(timezone.utc).replace(tzinfo=None)
    start_time = end_time - timedelta(days=args.days)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_path = OUTPUT_DIR / f"run_{run_id}"

    spark = (
        SparkSession.builder
        .appName("LakeWatchOnDemandAggregation")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    try:
        readings = spark.read.parquet(str(input_path))

        required = {"lake_id", "event_timestamp", *columns}
        missing = required - set(readings.columns)

        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        # Apply the requested rolling time range before aggregation.
        filtered = readings.filter(
            (F.col("event_timestamp") >= F.lit(start_time))
            & (F.col("event_timestamp") <= F.lit(end_time))
        )

        aggregations = [F.count("*").alias("reading_count")]

        for column in columns:
            aggregations.extend([
                F.avg(column).alias(f"avg_{column}"),
                F.min(column).alias(f"min_{column}"),
                F.max(column).alias(f"max_{column}"),
            ])

        summaries = (
            filtered
            .groupBy("lake_id")
            .agg(*aggregations)
        )

        # Save a separate Parquet dataset for this query.
        output_path.parent.mkdir(parents=True, exist_ok=True)

        summaries.write.mode("errorifexists").parquet(str(output_path))

        # Return the aggregates through the job runner as JSON.
        results = []
        for row in summaries.collect():
            record = row.asDict()
            results.append(record)

        response = {
            "run_id": run_id,
            "source_snapshot": input_path.name,
            "days": args.days,
            "columns": columns,
            "start_time": start_time.isoformat() + "Z",
            "end_time": end_time.isoformat() + "Z",
            "output_path": str(output_path),
            "lake_count": len(results),
            "results": results,
        }

        print("LAKEWATCH_RESULT=" + json.dumps(response, default=str))

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
