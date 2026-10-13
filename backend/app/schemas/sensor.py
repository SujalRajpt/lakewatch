from datetime import datetime
from pydantic import BaseModel


class SensorResponse(BaseModel):
    id: int
    sensor_id: str
    lake_id: str
    model: str
    firmware_version: str
    installation_date: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
