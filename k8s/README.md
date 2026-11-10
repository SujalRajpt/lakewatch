# Lakewatch Kubernetes Deployment

## Purpose

This directory contains Kubernetes resources for deploying Lakewatch to a local Kubernetes cluster managed by `kind`.

The existing Docker Compose deployment remains available as a separate development environment and reference.

## Architecture

The Kubernetes deployment will eventually include:

- PostgreSQL — persistent relational storage
- Kafka — sensor-reading message broker
- Kafka consumer workers — process readings from Kafka
- FastAPI backend — API and ingestion interface
- Sensor simulator — generate sensor readings
- Simulator UI — control the simulator
- Frontend — Lakewatch web interface
- Airflow — schedule data-lake exports
- Spark — distributed data processing

Resources will be introduced incrementally as each part of the deployment is implemented and tested.

## Directory Structure

- `postgres/` — database resources and persistent storage
- `kafka/` — broker and topic initialization resources
- `backend/` — FastAPI Deployment and Service
- `consumer/` — Kafka consumer Deployment
- `simulator/` — simulator Deployment and Service
- `frontend/` — frontend Deployment and Service
- `airflow/` — Airflow deployment and configuration
- `spark/` — Spark master, workers and job execution

## Local Cluster

The current development cluster is managed by `kind` and is named `lakewatch`.

Useful commands:

```bash
kind get clusters
kubectl config current-context
kubectl get nodes
kubectl get pods -A
```

## Deployment Principles

1. Reuse existing application code and Dockerfiles wherever practical.
2. Keep Kubernetes configuration separate from Docker Compose configuration.
3. Use ConfigMaps for non-sensitive configuration and Secrets for credentials.
4. Use Services for stable network endpoints.
5. Use persistent storage where data must survive Pod replacement.
6. Configure readiness and liveness probes where appropriate.
7. Deploy and verify components incrementally.
8. Avoid committing passwords, tokens or other secrets.
9. Document verification, troubleshooting and cleanup commands as resources are added.

## Current Status

- [x] Local `kind` cluster created and verified
- [x] Kubernetes project directory created
- [ ] Namespace and shared configuration
- [ ] PostgreSQL and Kafka
- [ ] Backend and consumer workers
- [ ] Simulator and frontend
- [ ] Airflow and Spark
- [ ] End-to-end verification
