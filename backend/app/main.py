from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import Base, engine, get_db
from app.models.lake import Lake
from app.models.sensor import Sensor
from app.models.reading import SensorReading
from app.schemas.reading import ReadingCreate, ReadingResponse


app = FastAPI()


# Create database tables
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-test")
def db_test():

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

    return {"database": "connected", "result": result.scalar()}


# --------------------------------------------------
# INGESTION
# --------------------------------------------------


@app.post("/api/readings", response_model=ReadingResponse, status_code=201)
def receive_reading(reading: ReadingCreate, db: Session = Depends(get_db)):

    # Check whether this event was already received
    existing = (
        db.query(SensorReading)
        .filter(SensorReading.event_id == reading.event_id)
        .first()
    )

    if existing:
        return existing

    new_reading = SensorReading(
        **reading.model_dump(), received_at=datetime.now(timezone.utc)
    )

    db.add(new_reading)
    db.commit()
    db.refresh(new_reading)

    return new_reading


# --------------------------------------------------
# SENSOR READINGS
# --------------------------------------------------


@app.get("/sensors/{sensor_id}/readings", response_model=list[ReadingResponse])
def get_sensor_readings(sensor_id: str, db: Session = Depends(get_db)):

    readings = (
        db.query(SensorReading)
        .filter(SensorReading.sensor_id == sensor_id)
        .order_by(SensorReading.event_timestamp.desc())
        .all()
    )

    return readings


# --------------------------------------------------
# LATEST SENSOR DATA
# --------------------------------------------------


@app.get("/sensors/{sensor_id}/data")
def get_sensor_data(sensor_id: str, db: Session = Depends(get_db)):

    latest = (
        db.query(SensorReading)
        .filter(SensorReading.sensor_id == sensor_id)
        .order_by(SensorReading.event_timestamp.desc())
        .first()
    )

    if latest is None:
        raise HTTPException(
            status_code=404, detail="Sensor not found or has no readings"
        )

    return {
        "sensor_id": sensor_id,
        "lake_id": latest.lake_id,
        "latest_reading": {
            "event_id": latest.event_id,
            "sequence_number": latest.sequence_number,
            "event_timestamp": latest.event_timestamp,
            "received_at": latest.received_at,
            "temperature": latest.temperature,
            "ph": latest.ph,
            "dissolved_oxygen": latest.dissolved_oxygen,
            "turbidity": latest.turbidity,
            "conductivity": latest.conductivity,
            "nitrate": latest.nitrate,
        },
    }


# --------------------------------------------------
# SENSOR STATUS
# --------------------------------------------------


@app.get("/sensors/{sensor_id}/status")
def get_sensor_status(sensor_id: str, db: Session = Depends(get_db)):

    latest = (
        db.query(SensorReading)
        .filter(SensorReading.sensor_id == sensor_id)
        .order_by(SensorReading.received_at.desc())
        .first()
    )

    if latest is None:
        raise HTTPException(status_code=404, detail="Sensor not found")

    now = datetime.now(timezone.utc)

    seconds_since_last_seen = (now - latest.received_at).total_seconds()

    if seconds_since_last_seen < 40:
        status = "online"

    elif seconds_since_last_seen < 120:
        status = "warning"

    else:
        status = "offline"

    return {
        "sensor_id": sensor_id,
        "status": status,
        "last_seen": latest.received_at,
        "last_sequence_number": latest.sequence_number,
    }
