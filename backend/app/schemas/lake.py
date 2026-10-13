from datetime import datetime
from pydantic import BaseModel


class LakeResponse(BaseModel):
    id: int
    lake_id: str
    name: str
    location: str
    created_at: datetime

    model_config = {"from_attributes": True}
