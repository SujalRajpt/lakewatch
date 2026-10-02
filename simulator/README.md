# LakeWatch Simulator

The LakeWatch Simulator is a Python-based simulation service for the LakeWatch project.

It simulates 10 independent lake sensors, continuously generates water-quality readings, and sends those readings to the LakeWatch FastAPI backend over HTTP.

The simulator also exposes its own FastAPI server for controlling and inspecting the simulated lakes.

## Architecture

```text
                         You / Swagger
                              |
                              | control
                              v
                    +----------------------+
                    |  LakeWatch Simulator |
                    |     FastAPI :9000    |
                    +----------+-----------+
                               |
                         HTTP / JSON
                               |
                               v
                    +----------------------+
                    |   LakeWatch Backend  |
                    |     FastAPI :8000    |
                    +----------+-----------+
                               |
                          SQLAlchemy
                               |
                               v
                         PostgreSQL
```

The simulator is intentionally separate from the backend.

- The simulator generates sensor readings.
- The simulator sends readings to the backend.
- The backend validates and stores the readings.
- The simulator does not access PostgreSQL.
- The simulator's control API is only used to manipulate the simulated environment.

## Features

### 1. Ten simulated lakes

| Lake | Sensor | Character |
|---|---|---|
| LAKE-001 | SENSOR-001 | Clean |
| LAKE-002 | SENSOR-002 | Sediment-heavy |
| LAKE-003 | SENSOR-003 | Nutrient-rich |
| LAKE-004 | SENSOR-004 | Polluted |
| LAKE-005 | SENSOR-005 | Clean |
| LAKE-006 | SENSOR-006 | Sediment-heavy |
| LAKE-007 | SENSOR-007 | Polluted |
| LAKE-008 | SENSOR-008 | Clean |
| LAKE-009 | SENSOR-009 | Nutrient-rich |
| LAKE-010 | SENSOR-010 | Moderate |

These are simulation profiles, not scientifically calibrated classifications of real lakes.

### 2. Individual lake stress controls

Every lake has an independent stress level:

```text
0%   = normal
100% = highly stressed
```

Changing LAKE-004 does not directly change the other lakes.

The stress level affects readings according to the lake's character.

### 3. Controlled randomness

The stress level controls the overall direction and intensity of the effect, while individual readings vary.

The simulator applies a random factor of approximately 85%–115% to the expected stress effect.

Conceptually:

```text
final effect =
    lake profile effect
    × stress intensity
    × random factor
```

The lake's main character remains consistent while individual readings are not identical.

### 4. Natural sensor drift

Even without stress, readings slowly change so the simulator does not produce identical values repeatedly.

### 5. Simulated time

```text
1 simulated day = 10 real minutes
```

Sensors generate readings every 5 simulated minutes, which is approximately every 2.08 real seconds.

Each cycle processes all 10 sensors.

## Project Structure

```text
simulator/
├── Dockerfile
├── requirements.txt
└── app/
    ├── main.py
    ├── config.py
    ├── metadata.py
    ├── readings.py
    ├── behaviors.py
    └── control.py
```

### File responsibilities

**`main.py`**
- Simulator FastAPI server
- Control endpoints
- Current-reading preview endpoint
- Background simulation loop
- Sending readings to the backend

**`config.py`**
- Backend API URL
- Simulation timing
- Failure-behavior switches
- Probabilities

**`metadata.py`**
- Simulated lake and sensor metadata
- Lake profiles

**`readings.py`**
- Sensor state
- Reading generation
- Natural drift
- Lake personality behavior
- Stress effects
- Controlled randomness

**`behaviors.py`**
- Missing readings
- Duplicate readings
- Malformed payloads
- Out-of-order timestamps
- Delayed events
- Random anomalies

**`control.py`**
- Current stress level for every lake

## Running with Docker

The simulator is normally run through the project's root `docker-compose.yml`.

The simulator exposes port `9000`.

```bash
docker compose up --build
```

Stop:

```bash
docker compose down
```

Example simulator service:

```yaml
simulator:
  build:
    context: ./simulator

  container_name: lakewatch-simulator

  ports:
    - "9000:9000"

  env_file:
    - .env

  depends_on:
    backend:
      condition: service_started
```

## Environment Variables

The simulator reads:

```env
API_URL=http://backend:8000/api/readings
```

Inside Docker Compose, `backend` refers to the FastAPI backend container.

The simulator therefore sends:

```text
POST http://backend:8000/api/readings
```

Do not use `localhost:8000` from inside the simulator container. Inside the simulator container, `localhost` refers to the simulator itself.

## Simulator Swagger UI

Once running:

```text
http://localhost:9000/docs
```

The LakeWatch backend has its own Swagger UI:

```text
http://localhost:8000/docs
```

## Simulator API

### Get all lakes

```http
GET /simulation/lakes
```

Returns the current configuration of all simulated lakes.

Example:

```json
[
  {
    "lake_id": "LAKE-001",
    "name": "Lake Azure",
    "profile": "clean",
    "stress_level": 0
  },
  {
    "lake_id": "LAKE-004",
    "name": "Lake Crystal",
    "profile": "polluted",
    "stress_level": 80
  }
]
```

### Get one lake

```http
GET /simulation/lakes/{lake_id}
```

Example:

```http
GET /simulation/lakes/LAKE-004
```

This returns the lake's control state, not a sensor reading.

### Change a lake's stress level

```http
POST /simulation/lakes/{lake_id}/control
```

Example:

```http
POST /simulation/lakes/LAKE-004/control
```

Request:

```json
{
  "stress_level": 80
}
```

Valid range:

```text
0 - 100
```

The change takes effect immediately for subsequent simulated readings.

### Preview a current reading

```http
GET /simulation/lakes/{lake_id}/current-reading
```

Example:

```http
GET /simulation/lakes/LAKE-004/current-reading
```

This generates a fresh reading using the lake's profile, current stress level, natural drift, and controlled randomness.

Preview readings are **not sent to the backend** and **not stored in PostgreSQL**.

A copy of the sensor state is used so previewing does not alter the real simulator sequence or state.

## Background Reading Pipeline

```text
Generate reading
      |
      v
Apply lake personality
      |
      v
Apply stress level
      |
      v
Apply controlled randomness
      |
      v
Apply optional failure behaviors
      |
      v
POST /api/readings
      |
      v
LakeWatch Backend
      |
      v
PostgreSQL
```

The simulator does not store reading history. The backend is responsible for persistent storage.

## Reading Format

A normal reading looks like:

```json
{
  "event_id": "uuid",
  "sensor_id": "SENSOR-004",
  "lake_id": "LAKE-004",
  "sequence_number": 37,
  "event_timestamp": "2026-10-01T14:50:15Z",
  "temperature": 25.9,
  "ph": 7.58,
  "dissolved_oxygen": 8.59,
  "turbidity": 1.64,
  "conductivity": 254.28,
  "nitrate": 3.0
}
```

The backend adds:

```text
received_at
```

when it receives the reading.

Thus:

```text
event_timestamp = when the simulated sensor produced the event
received_at     = when the backend received the event
```

## Data-Quality Simulation

All of these behaviors are disabled by default.

### Missing readings

```python
missing_readings_enabled = False
```

Some readings are deliberately not sent.

Useful for testing missing data, completeness calculations, and offline detection.

### Duplicate readings

```python
duplicate_readings_enabled = False
```

The same event can be sent more than once with the same `event_id`.

Useful for testing backend idempotency.

### Malformed payloads

```python
malformed_payloads_enabled = False
```

Possible cases include wrong data types, missing fields, and null values.

Useful for testing Pydantic validation and HTTP 422 responses.

### Out-of-order events

```python
out_of_order_enabled = False
```

An older event timestamp can arrive after a newer event.

Useful for testing sequence numbers, event timestamps, and ordering logic.

### Delayed events

```python
delayed_events_enabled = False
```

The simulator can deliberately wait before sending an event.

Useful for testing the difference between `event_timestamp` and `received_at`.

### Random anomalies

```python
anomalies_enabled = False
```

Some readings can contain extreme but valid values, such as unusually high/low pH, high turbidity, conductivity, nitrate, dissolved oxygen, or temperature.

This will eventually be useful for testing LakeWatch's alert system.

## Typical Development Workflow

1. Start the project:

```bash
docker compose up --build
```

2. Open simulator Swagger:

```text
http://localhost:9000/docs
```

3. Check Lake 004:

```http
GET /simulation/lakes/LAKE-004
```

4. Preview a reading:

```http
GET /simulation/lakes/LAKE-004/current-reading
```

5. Increase its stress level:

```http
POST /simulation/lakes/LAKE-004/control
```

```json
{
  "stress_level": 80
}
```

6. Preview again and compare the readings.

7. Check the real backend:

```text
http://localhost:8000/docs
```

or:

```text
http://localhost:8000/sensors/SENSOR-004/readings
```

The background simulator readings should continue appearing in the backend history.

## Design Principle

The simulator is a **fake external sensor system**.

It should not know about:

- PostgreSQL
- SQLAlchemy
- backend database models
- backend database queries

It only knows:

```text
HTTP
JSON
```

The backend is responsible for:

```text
Receive
Validate
Store
Query
Analyze
Alert
```

This separation makes LakeWatch closer to a real IoT/data-ingestion system and allows the backend to eventually consume data from something other than this simulator.
