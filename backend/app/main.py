import math
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone


from fastapi import Depends, FastAPI, HTTPException , Request
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select, text, func, literal, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.database.connection import get_db, initialize_database, engine
from app.models.lake import Lake
from app.models.sensor import Sensor
from app.models.reading import SensorReading
from app.schemas.reading import ReadingCreate, ReadingResponse, ReadingUpdate
from app.schemas.lake import LakeResponse
from app.schemas.sensor import SensorResponse
from app.services.data_quality import check_unexpected_interval,check_unexpected_gap, check_sequence_gap,check_out_of_order,check_delayed_reading
from app.services.idempotency import check_duplicate_event


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_database()
    yield
    await engine.dispose()


app = FastAPI(
    title="LakeWatch API",
    description="Lake and sensor monitoring API",
    version="1.0.0",
    lifespan=lifespan,
)

add_pagination(app)


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/dbtest")
async def db_test(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    return {"database": result.scalar()}

def sanitize_error(value):
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)

    if isinstance(value, dict):
        return {
            key: sanitize_error(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [sanitize_error(item) for item in value]

    return value


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={"detail": sanitize_error(exc.errors())},
    )


@app.post("/api/readings", response_model=ReadingResponse, status_code=201)
async def receive_reading(
    reading: ReadingCreate,
    db: AsyncSession = Depends(get_db),
):
    # 1. Check for duplicate events
    existing = await check_duplicate_event(db, reading)

    if existing:
        await db.commit()
        return existing
    received_at = datetime.now(timezone.utc)
    # 2. Create the new reading
    new_reading = SensorReading(
        **reading.model_dump(),
        received_at=datetime.now(timezone.utc),
    )

    # 3. Run all data-quality checks
    await check_sequence_gap(db, reading)
    await check_out_of_order(db, reading)
    await check_delayed_reading(db, reading, received_at)
    await check_unexpected_interval(db, reading)
    await check_unexpected_gap(db, reading)

    # 4. Add and save the reading and flags
    db.add(new_reading)

    await db.commit()
    await db.refresh(new_reading)

    return new_reading



# --------------------------------------------------
# READINGS
# --------------------------------------------------
# GET /api/lakes - Get information about all lakes
@app.get("/api/lakes", response_model=list[LakeResponse])
async def get_all_lake_info(db: AsyncSession = Depends(get_db)):
    query = select(Lake)
    result = await db.execute(query)
    return result.scalars().all()


# GET /api/lakes/{lake_id} - Get information about one lake
@app.get("/api/lakes/{lake_id}", response_model=LakeResponse)
async def get_lake_info(lake_id: str, db: AsyncSession = Depends(get_db)):
    query = select(Lake).where(Lake.lake_id == lake_id)
    result = await db.execute(query)
    lake = result.scalar_one_or_none()

    if lake is None:
        raise HTTPException(status_code=404, detail="Lake not found")

    return lake


# GET /api/sensors - Get information about all sensors
@app.get("/api/sensors", response_model=list[SensorResponse])
async def get_all_sensor_info(db: AsyncSession = Depends(get_db)):
    query = select(Sensor)
    result = await db.execute(query)
    return result.scalars().all()


# GET /api/sensors/{sensor_id} - Get information about one sensor
@app.get("/api/sensors/{sensor_id}", response_model=SensorResponse)
async def get_sensor_info(
    sensor_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = select(Sensor).where(Sensor.sensor_id == sensor_id)
    result = await db.execute(query)
    sensor = result.scalar_one_or_none()

    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")

    return sensor


# GET /api/lakes/{lake_id}/readings - Get paginated readings for a specific lake
@app.get("/api/lakes/{lake_id}/readings", response_model=Page[ReadingResponse])
async def get_lake_readings(
    lake_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = select(SensorReading).where(SensorReading.lake_id == lake_id)

    return await apaginate(db, query)


#latest reading for one lake
@app.get("/api/lakes/{lake_id}/latest-reading")
async def get_latest_reading(
    lake_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(SensorReading)
        .where(SensorReading.lake_id == lake_id)
        .order_by(SensorReading.event_timestamp.desc())
        .limit(1)
    )

    result = await db.execute(query)
    reading = result.scalar_one_or_none()

    if reading is None:
        raise HTTPException(
            status_code=404,
            detail="No readings found for this lake",
        )

    return reading



# GET /api/readings - Get all lake readings with pagination
@app.get("/api/readings", response_model=Page[ReadingResponse])
async def get_all_lake_readings(db: AsyncSession = Depends(get_db)):
    query = (
    select(SensorReading)
    .order_by(
        SensorReading.event_timestamp.desc(),
        SensorReading.id.desc()
        )
    )
    return await apaginate(db, query)


# GET /api/readings/42 - Get one specific reading by database ID
@app.get("/api/readings/{db_id}", response_model=ReadingResponse)
async def get_lake_by_db_id(db_id: int, db: AsyncSession = Depends(get_db)):
    query = select(SensorReading).where(SensorReading.id == db_id)
    result = await db.execute(query)
    row = result.scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="record not found")

    return row


# PUT /api/readings/{db_id} - Replace a specific reading
@app.put("/api/readings/{db_id}", response_model=ReadingResponse)
async def replace_reading(
    db_id: int,
    reading: ReadingCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SensorReading).where(SensorReading.id == db_id))
    row = result.scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="Reading not found")

    for key, value in reading.model_dump().items():
        setattr(row, key, value)

    await db.commit()
    await db.refresh(row)
    return row


# PATCH /api/readings/{db_id} - Partially update a specific reading
@app.patch("/api/readings/{db_id}", response_model=ReadingResponse)
async def update_reading(
    db_id: int,
    reading: ReadingUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SensorReading).where(SensorReading.id == db_id))
    row = result.scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="Reading not found")

    for key, value in reading.model_dump(exclude_unset=True).items():
        setattr(row, key, value)

    await db.commit()
    await db.refresh(row)
    return row


# DELETE /api/readings/{db_id} - Delete a specific reading
@app.delete("/api/readings/{db_id}")
async def delete_reading(
    db_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SensorReading).where(SensorReading.id == db_id))
    row = result.scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="Reading not found")

    await db.delete(row)
    await db.commit()

    return {"detail": "Reading deleted successfully"}


@app.get("/api/{lake_id}/aggregate")
async def get_agg(
    lake_id: str,
    db: AsyncSession = Depends(get_db),
):
    # 1. Calculate the cutoff
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=10)

    # 2. Align the cutoff to a five-minute boundary.
    # date_bin returns the start of the bucket containing cutoff.
    interval = literal_column("INTERVAL '5 minutes'")
    origin = literal(datetime(2000, 1, 1, tzinfo=timezone.utc))

    bucket_query = select(
        func.date_bin(interval, literal(cutoff), origin)
    )
    window_end = (await db.execute(bucket_query)).scalar_one()

    # The latest eligible window ends at window_end.
    window_start = window_end - timedelta(minutes=5)

    # 3. Check whether this lake has readings in that window.
    exists_query = select(
        func.count()
    ).select_from(SensorReading).where(
        SensorReading.lake_id == lake_id,
        SensorReading.event_timestamp >= window_start,
        SensorReading.event_timestamp < window_end,
    )

    count = (await db.execute(exists_query)).scalar_one()
    print(
    f"DEBUG lake_id={lake_id}, "
    f"window_start={window_start}, "
    f"window_end={window_end}, "
    f"count={count}"
)
    if count == 0:
        raise HTTPException(
            status_code=404,
            detail=(
                "No readings available for the eligible five-minute "
                "window yet. Retry later."
            ),
        )

    # 4. Aggregate the readings in PostgreSQL.
    bucket = func.date_bin(
        interval,
        SensorReading.event_timestamp,
        origin,
    ).label("window_start")

    query = (
        select(
            bucket,
            func.count().label("reading_count"),
            func.avg(SensorReading.temperature).label("avg_temperature"),
            func.min(SensorReading.temperature).label("min_temperature"),
            func.max(SensorReading.temperature).label("max_temperature"),
            func.avg(SensorReading.ph).label("avg_ph"),
            func.min(SensorReading.ph).label("min_ph"),
            func.max(SensorReading.ph).label("max_ph"),
            func.avg(SensorReading.dissolved_oxygen).label("avg_dissolved_oxygen"),
            func.avg(SensorReading.turbidity).label("avg_turbidity"),
            func.avg(SensorReading.conductivity).label("avg_conductivity"),
            func.avg(SensorReading.nitrate).label("avg_nitrate"),
        )
        .where(
            SensorReading.lake_id == lake_id,
            SensorReading.event_timestamp >= window_start,
            SensorReading.event_timestamp < window_end,
        )
        .group_by(bucket)
    )

    result = (await db.execute(query)).mappings().one()

    return {
        "lake_id": lake_id,
        "window_start": result["window_start"],
        "window_end": window_end,
        "reading_count": result["reading_count"],
        "temperature": {
            "avg": result["avg_temperature"],
            "min": result["min_temperature"],
            "max": result["max_temperature"],
        },
        "ph": {
            "avg": result["avg_ph"],
            "min": result["min_ph"],
            "max": result["max_ph"],
        },
        "dissolved_oxygen_avg": result["avg_dissolved_oxygen"],
        "turbidity_avg": result["avg_turbidity"],
        "conductivity_avg": result["avg_conductivity"],
        "nitrate_avg": result["avg_nitrate"],
    }