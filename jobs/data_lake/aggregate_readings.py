
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


INPUT_PATH = (
    "/workspace/data-lake/raw/"
    "sensor_readings_20261020T145422Z.parquet"
)

OUTPUT_PATH = "/workspace/data-lake/processed/five_minute_summaries"

REQUIRED_COLUMNS = [
    "lake_id",
    "event_timestamp",
    "temperature",
    "ph",
    "dissolved_oxygen",
    "turbidity",
    "conductivity",
    "nitrate",
]


def main():
    spark = (
        SparkSession.builder
        .appName("LakeWatchFiveMinuteSummary")
        .config(
            "spark.hadoop.fs.file.impl",
            "org.apache.hadoop.fs.RawLocalFileSystem",
        )
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    try:
        # Read only the selected raw snapshot.
        readings = spark.read.parquet(INPUT_PATH)

        # Validate that all required columns exist.
        missing = [
            column
            for column in REQUIRED_COLUMNS
            if column not in readings.columns
        ]

        if missing:
            raise ValueError(
                f"Missing required columns: {missing}"
            )

        print(f"Input: {INPUT_PATH}")
        print(f"Input columns: {readings.columns}")

        # Group readings by lake and five-minute event-time windows.
        summaries = (
            readings
            .groupBy(
                "lake_id",
                F.window(
                    F.col("event_timestamp"),
                    "5 minutes",
                ).alias("time_window"),
            )
            .agg(
                F.count("*").alias("reading_count"),

                F.avg("temperature").alias("avg_temperature"),
                F.min("temperature").alias("min_temperature"),
                F.max("temperature").alias("max_temperature"),

                F.avg("ph").alias("avg_ph"),
                F.min("ph").alias("min_ph"),
                F.max("ph").alias("max_ph"),

                F.avg("dissolved_oxygen").alias(
                    "avg_dissolved_oxygen"
                ),
                F.avg("turbidity").alias("avg_turbidity"),
                F.avg("conductivity").alias("avg_conductivity"),
                F.avg("nitrate").alias("avg_nitrate"),
            )
            .select(
                "lake_id",
                F.col("time_window.start").alias("window_start"),
                F.col("time_window.end").alias("window_end"),
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
            )
        )

        # Materialize the results once so diagnostics can reuse them.
        summaries = summaries.cache()
        summary_count = summaries.count()

        # Replace only this dedicated output directory.
        (
            summaries.write
            .mode("overwrite")
            .parquet(OUTPUT_PATH)
        )

        print(f"Summaries written to: {OUTPUT_PATH}")
        print(f"Summary rows: {summary_count}")

        # Display a sample of the saved summary data.
        summaries.orderBy(
            "lake_id",
            "window_start",
        ).show(10, truncate=False)

        summaries.unpersist()

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
