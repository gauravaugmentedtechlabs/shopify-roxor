from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.enums import ProcessingStatus
from app.models.mixins import TimestampMixin

class RetryQueue(TimestampMixin, Base):
    """Generic retry queue with exponential backoff and dead-letter state."""
    __tablename__ = "retry_queue"
    id: Mapped[int] = mapped_column(primary_key=True)
    operation_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    status: Mapped[ProcessingStatus] = mapped_column(Enum(ProcessingStatus), default=ProcessingStatus.pending, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[str | None] = mapped_column(String(128))
