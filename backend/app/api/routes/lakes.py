from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.lake import Lake
from app.models.reading import SensorReading
from app.schemas.lake import LakeResponse
from app.schemas.reading import ReadingResponse

router = APIRouter(prefix="/api/lakes", tags=["lakes"])


@router.get("", response_model=list[LakeResponse])
async def get_all_lake_info(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lake))
    return result.scalars().all()


@router.get("/{lake_id}", response_model=LakeResponse)
async def get_lake_info(lake_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lake).where(Lake.lake_id == lake_id))
    lake = result.scalar_one_or_none()

    if lake is None:
        raise HTTPException(status_code=404, detail="Lake not found")

    return lake


@router.get("/{lake_id}/readings", response_model=Page[ReadingResponse])
async def get_lake_readings(
    lake_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = select(SensorReading).where(SensorReading.lake_id == lake_id)
    return await apaginate(db, query)


@router.get("/{lake_id}/latest-reading")
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
