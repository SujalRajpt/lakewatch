from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.sensor import Sensor
from app.schemas.sensor import SensorResponse

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


@router.get("", response_model=list[SensorResponse])
async def get_all_sensor_info(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Sensor))
    return result.scalars().all()


@router.get("/{sensor_id}", response_model=SensorResponse)
async def get_sensor_info(
    sensor_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Sensor).where(Sensor.sensor_id == sensor_id)
    )
    sensor = result.scalar_one_or_none()

    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")

    return sensor
