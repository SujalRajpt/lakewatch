
"""Export a consistent PostgreSQL snapshot to a raw Parquet file."""

import os
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import psycopg
from psycopg.rows import dict_row


OUTPUT_DIR = Path(os.getenv("DATA_LAKE_RAW_DIR", "/data-lake/raw"))

COLUMNS = [
    "id",
    "event_id",
    "sensor_id",
    "lake_id",
    "sequence_number",
    "event_timestamp",
    "received_at",
    "temperature",
    "ph",
    "dissolved_oxygen",
    "turbidity",
    "conductivity",
    "nitrate",
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Use the same PostgreSQL environment variables as the backend.
    with psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        row_factory=dict_row,
    ) as conn:
        # Keep the count and export consistent while readings arrive.
        with conn.transaction():
            conn.execute(
                "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
            )

            total = conn.execute(
                "SELECT COUNT(*) AS count FROM sensor_readings"
            ).fetchone()["count"]

            rows = conn.execute(
                """
                SELECT id, event_id, sensor_id, lake_id, sequence_number,
                       event_timestamp, received_at, temperature, ph,
                       dissolved_oxygen, turbidity, conductivity, nitrate
                FROM sensor_readings
                ORDER BY id
                """
            ).fetchall()

            if len(rows) != total:
                raise RuntimeError(
                    f"Count mismatch: expected {total}, read {len(rows)}"
                )

            # Preserve the table's column order in the Parquet output.
            table = pa.Table.from_pylist(
                [{column: row[column] for column in COLUMNS} for row in rows]
            )

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_file = OUTPUT_DIR / f"sensor_readings_{timestamp}.parquet"

        pq.write_table(table, output_file, compression="snappy")

    # Read the output back to verify that the file is valid.
    exported = pq.read_table(output_file)

    if exported.num_rows != total:
        output_file.unlink(missing_ok=True)
        raise RuntimeError("Exported Parquet row count does not match PostgreSQL")

    print(f"PostgreSQL rows: {total}")
    print(f"Parquet rows:    {exported.num_rows}")
    print(f"Columns:         {exported.num_columns}")
    print(f"Output:          {output_file}")


if __name__ == "__main__":
    main()
