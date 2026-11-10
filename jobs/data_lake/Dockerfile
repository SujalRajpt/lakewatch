FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir "psycopg[binary]" pyarrow

COPY export_readings.py /jobs/data_lake/export_readings.py

CMD ["python", "/jobs/data_lake/export_readings.py"]
