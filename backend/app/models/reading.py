from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    event_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    sensor_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    lake_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    temperature: Mapped[float] = mapped_column(Float, nullable=False)

    ph: Mapped[float] = mapped_column(Float, nullable=False)

    dissolved_oxygen: Mapped[float] = mapped_column(Float, nullable=False)

    turbidity: Mapped[float] = mapped_column(Float, nullable=False)

    conductivity: Mapped[float] = mapped_column(Float, nullable=False)

    nitrate: Mapped[float] = mapped_column(Float, nullable=False)
