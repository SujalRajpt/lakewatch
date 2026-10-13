from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DataQualityFlag(Base):
    __tablename__ = "data_quality_flags"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    reading_id: Mapped[int | None] = mapped_column(
        ForeignKey("sensor_readings.id"),
        nullable=True,
    )

    sensor_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    event_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True,
    )

    rule_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    details: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )