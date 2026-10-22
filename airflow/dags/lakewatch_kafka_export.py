
"""Airflow DAG for scheduled Lakewatch PostgreSQL-to-Parquet exports."""

import logging
import sys
from datetime import timedelta
from pathlib import Path

import pendulum

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.models import Variable
from airflow.hooks.base import BaseHook
from airflow.operators.python import PythonOperator


# The Compose mount makes jobs available at /jobs inside Airflow.
sys.path.insert(0, "/jobs")

from data_lake.export_readings_automated import export_readings


DAG_ID = "lakewatch_kafka_export"
POSTGRES_CONN_ID = "lakewatch_postgres"


def read_export_config():
    """Read non-secret workflow settings from Airflow Variables."""

    enabled = Variable.get(
        "lakewatch_export_enabled",
        default_var="true",
    ).strip().lower()

    if enabled not in {"true", "false"}:
        raise AirflowException(
            "lakewatch_export_enabled must be true or false"
        )

    raw_dir = Variable.get(
        "lakewatch_raw_dir",
        default_var="/data-lake/raw",
    )

    return {
        "enabled": enabled == "true",
        "raw_dir": raw_dir,
        "demo_message": "Hello from Airflow XCom!",
    }


def run_export(ti):
    """Read upstream configuration and export using an Airflow Connection."""

    config = ti.xcom_pull(task_ids="read_export_config")
    logging.info("XCom demo message: %s", config["demo_message"])

    if not config["enabled"]:
        logging.info("Lakewatch export is disabled; skipping export.")
        return {
            "status": "skipped",
            "reason": "Export disabled by Airflow Variable",
        }

    connection = BaseHook.get_connection(POSTGRES_CONN_ID)

    if not connection.host or not connection.login or not connection.schema:
        raise AirflowException(
            f"Airflow Connection {POSTGRES_CONN_ID!r} needs "
            "a host, username, and database name"
        )

    connection_params = {
        "host": connection.host,
        "port": connection.port or 5432,
        "dbname": connection.schema,
        "user": connection.login,
        "password": connection.password or "",
        "connect_timeout": 15,
    }

    # Optional PostgreSQL settings can be supplied in Connection Extra.
    extra = connection.extra_dejson
    if extra.get("sslmode"):
        connection_params["sslmode"] = extra["sslmode"]

    result = export_readings(
        connection_params=connection_params,
        output_dir=config["raw_dir"],
    )

    result["status"] = "success"
    return result


def report_export(ti):
    """Demonstrate XCom by consuming the export task's return value."""

    result = ti.xcom_pull(task_ids="run_export")

    if not result:
        raise AirflowException("No export metadata was received through XCom")

    if result["status"] == "skipped":
        logging.info("Export skipped: %s", result["reason"])
        return

    logging.info("Export completed successfully")
    logging.info("Output file: %s", result["output_path"])
    logging.info("Rows exported: %s", result["row_count"])
    logging.info("Columns: %s", result["column_count"])
    logging.info("File size: %s bytes", result["file_size_bytes"])
    logging.info("Export time: %s", result["exported_at_utc"])


with DAG(
    dag_id=DAG_ID,
    description="Export a consistent Lakewatch PostgreSQL snapshot to Parquet",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    schedule="0 */12 * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "lakewatch",
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
    },
    tags=["lakewatch", "kafka", "data-lake"],
) as dag:

    config_task = PythonOperator(
        task_id="read_export_config",
        python_callable=read_export_config,
    )

    export_task = PythonOperator(
        task_id="run_export",
        python_callable=run_export,
    )

    report_task = PythonOperator(
        task_id="report_export",
        python_callable=report_export,
    )

    config_task >> export_task >> report_task
