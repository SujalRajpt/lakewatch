
"""Export a consistent PostgreSQL snapshot to a raw Parquet file.

Designed for orchestration by Airflow. Database credentials are supplied
by the caller and are never written to the output or returned as XCom.
"""

from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import psycopg
from psycopg.rows import dict_row


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


def export_readings(connection_params: dict, output_dir: str) -> dict:
    """Export a consistent snapshot and return small, serializable metadata."""

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    with psycopg.connect(
        **connection_params,
        row_factory=dict_row,
    ) as conn:
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

            table = pa.Table.from_pylist(
                [
                    {column: row[column] for column in COLUMNS}
                    for row in rows
                ]
            )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_file = destination / f"sensor_readings_{timestamp}.parquet"

    pq.write_table(table, output_file, compression="snappy")

    exported = pq.read_table(output_file)

    if exported.num_rows != total:
        output_file.unlink(missing_ok=True)
        raise RuntimeError(
            "Exported Parquet row count does not match PostgreSQL"
        )

    return {
        "output_path": str(output_file),
        "row_count": exported.num_rows,
        "column_count": exported.num_columns,
        "file_size_bytes": output_file.stat().st_size,
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
    }
