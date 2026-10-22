
FROM apache/spark:3.5.0

USER root

# Install Python and pip for PySpark jobs
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir fastapi uvicorn

# Configure Spark and Python
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3
ENV SPARK_HOME=/opt/spark

WORKDIR /workspace

EXPOSE 7077 8080 8081

CMD ["bash"]
