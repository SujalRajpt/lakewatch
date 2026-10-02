# LakeWatch Sensor Simulator — Documentation

## 1. What is the Simulator?

The LakeWatch Simulator is a standalone FastAPI application that simulates a network of sensors installed across multiple lakes.

Its job is to continuously generate realistic sensor readings and send them to the LakeWatch backend API.

The simulator is designed to behave like a real-world sensor system, including:

- Multiple lakes
- Multiple sensors per lake
- Continuous sensor readings
- Different lake characteristics
- Natural variation in sensor values
- Missing readings
- Duplicate readings
- Malformed payloads
- Out-of-order events
- Delayed events
- Anomalous sensor values
- Concurrent requests
- Burst traffic

The simulator is controlled through its own FastAPI API, so most behavior can be changed without modifying the Python code.


## 2. Architecture

The overall flow is:

    Sensor Simulator
          │
          │ HTTP POST
          ▼
    LakeWatch Backend
          │
          │ SQLAlchemy
          ▼
    PostgreSQL


The simulator itself does NOT directly access PostgreSQL.

It generates sensor data and sends it to the backend.

The backend is responsible for:

- Receiving the data
- Validating the request
- Processing the reading
- Storing it in PostgreSQL


The simulator has its own FastAPI application, which is used only to control and inspect the simulation.


## 3. Services and Ports

When running with Docker Compose:

    Service      Purpose                         Port
    ------------------------------------------------
    backend      LakeWatch backend API          8000
    simulator    Simulator control API          9000
    postgres     PostgreSQL database            5432
    adminer      Database administration UI     8080


Important:

Port 9000 is NOT the backend.

Port 9000 is the simulator's control API.

The simulator sends sensor readings to the backend running on port 8000.


## 4. Starting the Project

From the project root:

    docker compose up --build

To run in the background:

    docker compose up --build -d

The main services are then:

    Backend:
    http://localhost:8000

    Backend Swagger:
    http://localhost:8000/docs

    Simulator:
    http://localhost:9000

    Simulator Swagger:
    http://localhost:9000/docs

    Adminer:
    http://localhost:8080


The simulator starts automatically with the Docker Compose stack.


## 5. How Sensor Data Is Generated

The simulator creates metadata for the lakes and sensors when it starts.

Each sensor maintains its own state.

Every simulation cycle:

1. A reading is generated for each sensor.
2. The sensor sequence number is incremented.
3. Natural variation is applied to the sensor values.
4. The lake's characteristics and stress level affect the reading.
5. A unique event ID is generated.
6. An event timestamp is generated.
7. The reading is sent to the backend.


A normal reading contains:

    event_id
    sensor_id
    lake_id
    sequence_number
    event_timestamp
    temperature
    ph
    dissolved_oxygen
    turbidity
    conductivity
    nitrate


## 6. Normal Sensor Ranges

Sensors start with values generated around these ranges:

    Temperature:       22–28
    pH:                6.8–7.8
    Dissolved Oxygen:  6–9
    Turbidity:         1–5
    Conductivity:      200–500
    Nitrate:           1–5


These are starting ranges, not fixed limits.

Values naturally change between readings.

Lake characteristics and lake stress can also modify the generated values.


## 7. Sensor Sequence Numbers

Every sensor maintains its own sequence number.

For example:

    SENSOR-001
    sequence 1
    sequence 2
    sequence 3
    sequence 4
    ...

The sequence number increases whenever a reading is generated.

This allows the backend or future data-processing systems to reason about the order of readings from a sensor.


## 8. Event IDs

Every generated reading normally receives a UUID-based `event_id`.

Example:

    "event_id": "8e1c7f3e-...."

The event ID identifies the individual event.

It is different from the sensor sequence number.

A sequence number describes the position of a reading for a sensor, while the event ID identifies the event itself.


## 9. Event Timestamp

Every reading contains an `event_timestamp`.

This represents when the simulated sensor event occurred.

The simulator can intentionally modify this timestamp when out-of-order or delayed-event behavior is enabled.

This is important because real distributed systems cannot always assume that events arrive at the backend in the same order in which they occurred.


## 10. Lakes and Lake Characteristics

The simulator supports multiple lakes.

Each lake can have its own characteristics/profile.

These characteristics influence the sensor readings generated for sensors belonging to that lake.

The simulator also maintains a lake stress value.

Lake stress can be changed through the simulator control API and affects the generated readings.

This makes it possible to simulate different environmental conditions without changing the underlying sensor-generation code.


## 11. Data Quality Behaviors

The simulator can intentionally generate imperfect data.

These behaviors are controlled through the simulator API.

The available behaviors are:

    Missing readings
    Duplicate readings
    Malformed payloads
    Out-of-order events
    Delayed events
    Anomalies


Each behavior has:

    enabled/disabled

and, where applicable:

    probability/rate


A rate of:

    0.0

means the behavior will never trigger.

A rate of:

    1.0

means it will trigger whenever the corresponding behavior is evaluated.


## 12. Missing Readings

Missing-reading behavior simulates a sensor failing to send a reading.

Instead of every generated reading reaching the backend, some readings are skipped.

This represents situations such as:

- Sensor communication failure
- Network problems
- Temporary sensor downtime
- Lost events


The important point is that a missing reading does not mean a malformed reading was sent.

No request is sent for the dropped event.


## 13. Duplicate Readings

Duplicate behavior simulates the same sensor event being delivered more than once.

This represents situations such as:

- Network retries
- Message redelivery
- Client retries
- Duplicate event delivery


Duplicate events are particularly useful for systems that need idempotency.

The backend should be able to recognize that an event has already been processed instead of incorrectly treating the duplicate as a completely new event.


## 14. Malformed Payloads

Malformed behavior intentionally creates invalid requests.

The simulator currently supports three malformed cases:

    1. Wrong type
    2. Missing field
    3. Null value


Examples include:

    temperature = "not-a-number"

or:

    ph is removed

or:

    nitrate = null


These payloads are still sent to the backend.

The backend's Pydantic validation is responsible for rejecting them.


## 15. Out-of-Order Events

Out-of-order behavior modifies the event timestamp.

The simulator moves the event timestamp backwards by five simulated minutes.

For example, a later-generated event may contain an earlier timestamp.

This simulates events arriving in an order different from their actual event time.

This is important for future processing systems because:

    event generation order
            ≠
    event arrival order
            ≠
    event timestamp order


## 16. Delayed Events

Delayed-event behavior causes an event to be sent later than normal.

This simulates network or processing delays.

A delayed event may therefore arrive at the backend after newer events have already been processed.

This is different from an out-of-order event:

    Out-of-order:
    The timestamp is intentionally older.

    Delayed:
    The event itself is intentionally sent later.


## 17. Anomalies

Anomaly behavior generates sensor values outside their normal operating range.

The simulator can create anomalous values for:

    temperature
    pH
    dissolved oxygen
    turbidity
    conductivity
    nitrate


Examples include extremely high or low values such as:

    Temperature:       45, 50, or 5
    pH:                2.5, 3, 11, or 12
    Dissolved Oxygen:  0.2, 0.5, or 15
    Turbidity:         30–60
    Conductivity:      1000–2000
    Nitrate:           20–50


An anomaly is still a structurally valid reading.

That means an anomalous value is different from a malformed payload.

For example:

    temperature = 50

can be a valid numeric payload containing an abnormal value.

Whereas:

    temperature = "not-a-number"

is a malformed payload.


## 18. Concurrency

The simulator can send multiple readings concurrently.

Concurrency is controlled through:

    enabled
    mode
    interval


`mode` determines how many requests are sent concurrently in a batch.

For example:

    mode = 10

means the simulator can send up to 10 generated requests concurrently in a batch.


This is useful for simulating multiple sensors transmitting at approximately the same time.

The simulator uses asynchronous HTTP requests and `asyncio.gather()` to send these requests concurrently.


## 19. Burst Traffic

Burst mode is designed to simulate sudden traffic spikes.

Instead of sending readings at the normal rate, the simulator creates a burst of payloads and sends them concurrently.

Burst configuration contains:

    enabled
    size
    interval


For example:

    size = 100

means the simulator attempts to send 100 requests concurrently during a burst.


Burst mode has priority over normal concurrency mode.

The order is:

    Burst enabled
        ↓
    use Burst mode

    Otherwise, if Concurrency enabled
        ↓
    use Concurrency mode

    Otherwise
        ↓
    normal sequential sending


Burst payloads are created by copying generated payloads.

Therefore, burst mode is primarily intended to simulate high request volume and traffic pressure rather than represent 100 completely independent sensor events.


## 20. Simulation Timing

The simulator represents a simulated 24-hour day using a configurable amount of real time.

The important configuration values are:

    simulated_day_seconds
    reading_interval_simulated_minutes


For example, with:

    simulated_day_seconds = 600
    reading_interval_simulated_minutes = 5

five simulated minutes correspond to approximately:

    2.08 real seconds


With 10 sensors, this produces roughly 10 sensor-reading requests every normal simulation cycle.


## 21. Simulator Control API

The simulator provides its own API on port 9000.

Swagger documentation:

    http://localhost:9000/docs


### Health

    GET /health

Used to check whether the simulator is running.


### View Lakes

    GET /simulation/lakes

Returns information about the simulated lakes.


### View One Lake

    GET /simulation/lakes/{lake_id}

Returns information about a specific lake.


### Control a Lake

    POST /simulation/lakes/{lake_id}/control

Used to change lake-level simulation controls such as the lake's stress state.


### Current Reading

    GET /simulation/lakes/{lake_id}/current-reading

Returns the current simulated reading for a lake.


### View Behaviors

    GET /simulation/behaviors

Returns the current data-quality behavior configuration.


### Control Behaviors

    POST /simulation/behaviors/control

Used to enable/disable behaviors and change their rates.


### View Concurrency

    GET /simulation/concurrency

Returns the current concurrency configuration.


### Control Concurrency

    POST /simulation/concurrency/control

Used to enable/disable concurrent request generation and configure the batch size.


### View Burst Configuration

    GET /simulation/burst

Returns the current burst configuration.


### Control Burst

    POST /simulation/burst/control

Used to enable/disable burst traffic and configure burst size and interval.


## 22. Example: Enabling Malformed Payloads

The simulator control API can be used without changing Python code.

Example:

    curl -X POST http://localhost:9000/simulation/behaviors/control \
      -H "Content-Type: application/json" \
      -d '{
        "malformed_payloads_enabled": true,
        "malformed_payload_rate": 1.0
      }'


The same approach can be used for the other behavior controls.

After changing a configuration, the simulator applies the new behavior while it is running.


## 23. Environment Configuration

Simulator configuration is kept outside the Python source where possible.

The `.env` file is used to control configuration such as:

    Backend API URL
    Number/timing of simulated cycles
    Reading interval
    Simulator behavior settings


This allows the simulation environment to be changed without modifying the simulator's core logic.


## 24. Logs

The simulator prints useful information to its Docker logs.

For example:

    [SENT]
    Indicates a reading was sent to the backend.

    [ERROR]
    Indicates that sending the request encountered an error.

    [BURST]
    Indicates that a burst is being sent.

    [BURST COMPLETE]
    Indicates that the burst sending operation has completed.

The backend logs can be used separately to see how the backend responded to incoming requests.


To view simulator logs:

    docker compose logs -f simulator


To view backend logs:

    docker compose logs -f backend


## 25. Database Relationship

The simulator does not know or care how PostgreSQL stores the data.

Its responsibility ends at sending HTTP requests to:

    http://backend:8000/api/readings

inside Docker Compose.


The backend then handles:

    HTTP request
        ↓
    Pydantic validation
        ↓
    SQLAlchemy
        ↓
    PostgreSQL


This separation is intentional.

It allows the simulator to behave like an external collection of real sensors rather than becoming tightly coupled to the backend database.


## 26. Important Concepts Before Working on the Backend

When building the backend, keep the following distinctions clear:

### Event ID

Identifies an individual event.

    event_id


### Sensor ID

Identifies the sensor that generated the event.

    sensor_id


### Lake ID

Identifies the lake where the sensor exists.

    lake_id


### Sequence Number

Represents the reading sequence for a particular sensor.

    sequence_number


### Event Timestamp

Represents when the simulated event occurred.

    event_timestamp


### Received Timestamp

This should be generated by the backend when it receives the request.

    received_at


These timestamps are intentionally different.

For example:

    Sensor event happens
            ↓
    event_timestamp
            ↓
    network delay
            ↓
    backend receives event
            ↓
    received_at


This distinction becomes important when dealing with delayed and out-of-order events.


## 27. Important Backend Considerations

The simulator intentionally produces situations that a real backend may encounter.

The backend should therefore be designed with:

- Request validation
- Database constraints
- Event uniqueness/idempotency
- Proper handling of duplicate events
- Correct timestamp handling
- Handling of late events
- Handling of abnormal but valid values
- Error handling
- Database transaction management
- Concurrent requests


The simulator should be treated as an external producer of events.

The backend should not depend on the simulator's internal Python implementation.


## 28. Recommended Mental Model

Think of the simulator as:

    "A group of fake sensors connected to the internet."


Each sensor:

    generates data
          ↓
    sends data
          ↓
    may fail
          ↓
    may send duplicates
          ↓
    may send bad data
          ↓
    may send late data
          ↓
    may suddenly send many events


The backend's job is to reliably handle whatever arrives.


## 29. Quick Start

Start everything:

    docker compose up --build


Open:

    Backend:
    http://localhost:8000/docs

    Simulator:
    http://localhost:9000/docs

    Adminer:
    http://localhost:8080


Watch simulator activity:

    docker compose logs -f simulator


Watch backend activity:

    docker compose logs -f backend


The simulator will automatically generate sensor readings and send them to the backend according to its configuration.


## 30. Key Takeaway

The LakeWatch Simulator is a configurable event producer.

Its primary purpose is to provide the backend with realistic sensor traffic rather than simply generating random numbers.

It models:

    Sensors
      ↓
    Sensor readings
      ↓
    Different lakes and environmental conditions
      ↓
    Normal traffic
      ↓
    Concurrent traffic
      ↓
    Burst traffic
      ↓
    Real-world data problems
          ├── missing events
          ├── duplicates
          ├── malformed data
          ├── late events
          ├── out-of-order events
          └── anomalous values
      ↓
    Backend API


The simulator should therefore be considered an independent data-producing service whose job is to continuously create and deliver events to LakeWatch.