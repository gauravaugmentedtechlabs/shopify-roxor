from datetime import datetime
from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.enums import FileDirection, ProcessingStatus
from app.models.mixins import TimestampMixin

class ProcessedFile(TimestampMixin, Base):
    """Tracks XML files and enforces file-hash idempotency."""
    __tablename__ = "processed_files"
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    remote_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    archive_path: Mapped[str | None] = mapped_column(String(1024))
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    idoc_type: Mapped[str] = mapped_column(String(32), nullable=False)
    direction: Mapped[FileDirection] = mapped_column(Enum(FileDirection), nullable=False)
    status: Mapped[ProcessingStatus] = mapped_column(Enum(ProcessingStatus), default=ProcessingStatus.pending, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    correlation_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
