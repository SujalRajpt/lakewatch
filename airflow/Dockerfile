FROM apache/airflow:2.10.5

USER root
RUN mkdir -p /jobs/data_lake

USER airflow

RUN pip install --no-cache-dir \
    "psycopg[binary]" \
    "psycopg2-binary" \
    "pyarrow"

COPY --chown=airflow:root airflow/dags /opt/airflow/dags

COPY --chown=airflow:root \
    jobs/data_lake/export_readings_automated.py \
    /jobs/data_lake/export_readings_automated.py