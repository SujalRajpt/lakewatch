from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Sensor(Base):
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    sensor_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    lake_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("lakes.lake_id"),
        nullable=False,
    )

    model: Mapped[str] = mapped_column(String, nullable=False)

    firmware_version: Mapped[str] = mapped_column(String, nullable=False)

    installation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
