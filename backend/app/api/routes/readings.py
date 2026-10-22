from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.reading import SensorReading
from app.schemas.reading import ReadingCreate, ReadingResponse, ReadingUpdate

router = APIRouter(prefix="/api", tags=["readings"])


@router.post("/readings", status_code=status.HTTP_202_ACCEPTED)
async def receive_reading(reading: ReadingCreate, request: Request):
    message = {
        "reading": reading.model_dump(mode="json"),
        "received_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        await request.app.state.kafka_producer.send_and_wait(
            "sensor-readings",
            key=str(reading.sensor_id),
            value=message,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not publish reading to Kafka",
        ) from exc

    # Accepted by Kafka, not necessarily persisted to PostgreSQL yet.
    return {
        "status": "accepted",
        "event_id": str(reading.event_id),
    }


@router.get("/readings", response_model=Page[ReadingResponse])
async def get_all_lake_readings(db: AsyncSession = Depends(get_db)):
    query = select(SensorReading).order_by(
        SensorReading.event_timestamp.desc(),
        SensorReading.id.desc(),
    )
    return await apaginate(db, query)


@router.get("/readings/{db_id}", response_model=ReadingResponse)
async def get_lake_by_db_id(
    db_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SensorReading).where(SensorReading.id == db_id)
    )
    row = result.scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="record not found")

    return row


@router.put("/readings/{db_id}", response_model=ReadingResponse)
async def replace_reading(
    db_id: int,
    reading: ReadingCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SensorReading).where(SensorReading.id == db_id)
    )
    row = result.scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="Reading not found")

    for key, value in reading.model_dump().items():
        setattr(row, key, value)

    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/readings/{db_id}", response_model=ReadingResponse)
async def update_reading(
    db_id: int,
    reading: ReadingUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SensorReading).where(SensorReading.id == db_id)
    )
    row = result.scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="Reading not found")

    for key, value in reading.model_dump(exclude_unset=True).items():
        setattr(row, key, value)

    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/readings/{db_id}")
async def delete_reading(
    db_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SensorReading).where(SensorReading.id == db_id)
    )
    row = result.scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="Reading not found")

    await db.delete(row)
    await db.commit()

    return {"detail": "Reading deleted successfully"}
