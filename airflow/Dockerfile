
FROM apache/airflow:2.10.5

# Install the libraries used by the existing Parquet export script.
RUN pip install --no-cache-dir \
    "psycopg[binary]" \
    "pyarrow"
