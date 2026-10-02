from datetime import datetime

from pydantic import BaseModel


class ReadingCreate(BaseModel):
    event_id: str
    sensor_id: str
    lake_id: str
    sequence_number: int
    event_timestamp: datetime

    temperature: float
    ph: float
    dissolved_oxygen: float
    turbidity: float
    conductivity: float
    nitrate: float


class ReadingResponse(ReadingCreate):
    id: int
    received_at: datetime

    model_config = {"from_attributes": True}
