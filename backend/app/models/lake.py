from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Lake(Base):
    __tablename__ = "lakes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    lake_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False)

    location: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
