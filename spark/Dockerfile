
FROM apache/spark:3.5.0

USER root

RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir fastapi uvicorn

ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3
ENV SPARK_HOME=/opt/spark

# Package the existing Lakewatch Spark code into the image.
WORKDIR /workspace

COPY spark/job_runner.py /workspace/spark/job_runner.py
COPY jobs/data_lake/on_demand_aggregate.py /workspace/jobs/data_lake/on_demand_aggregate.py
COPY jobs/data_lake/aggregate_readings.py /workspace/jobs/data_lake/aggregate_readings.py
EXPOSE 7077 8080 8081 9002

CMD ["bash"]
