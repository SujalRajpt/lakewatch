
from datetime import datetime

from pydantic import BaseModel, Field


class ReadingCreate(BaseModel):
    event_id: str
    sensor_id: str
    lake_id: str
    sequence_number: int = Field(ge=0)
    event_timestamp: datetime

    temperature: float = Field(ge=-5, le=60)
    ph: float = Field(ge=0, le=14)
    dissolved_oxygen: float = Field(ge=0, le=25)
    turbidity: float = Field(ge=0, le=1000)
    conductivity: float = Field(ge=0, le=10000)
    nitrate: float = Field(ge=0, le=100)


class ReadingResponse(ReadingCreate):
    id: int
    received_at: datetime

    model_config = {"from_attributes": True}


class ReadingUpdate(BaseModel):
    event_id: str | None = None
    sensor_id: str | None = None
    lake_id: str | None = None

    sequence_number: int | None = Field(default=None, ge=0)
    event_timestamp: datetime | None = None

    temperature: float | None = Field(default=None, ge=-5, le=60)
    ph: float | None = Field(default=None, ge=0, le=14)
    dissolved_oxygen: float | None = Field(default=None, ge=0, le=25)
    turbidity: float | None = Field(default=None, ge=0, le=1000)
    conductivity: float | None = Field(default=None, ge=0, le=10000)
    nitrate: float | None = Field(default=None, ge=0, le=100)
