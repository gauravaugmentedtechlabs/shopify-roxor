from sqlalchemy import select
from app.models import FileDirection, ProcessedFile, ProcessingStatus
from app.repositories.base import Repository
from app.utils.time import utcnow

class ProcessedFileRepository(Repository):
    """Persistence for file idempotency and state transitions."""
    async def by_hash(self, file_hash: str) -> ProcessedFile | None:
        return (await self.session.execute(select(ProcessedFile).where(ProcessedFile.file_hash == file_hash))).scalar_one_or_none()

    async def create(self, *, filename: str, remote_path: str, file_hash: str, idoc_type: str, direction: FileDirection, correlation_id: str, status: ProcessingStatus = ProcessingStatus.processing) -> ProcessedFile:
        model = ProcessedFile(filename=filename, remote_path=remote_path, file_hash=file_hash, idoc_type=idoc_type, direction=direction, correlation_id=correlation_id, status=status, first_seen_at=utcnow())
        self.session.add(model); await self.session.flush(); return model

    async def mark_complete(self, model: ProcessedFile, status: ProcessingStatus, archive_path: str | None = None, error: str | None = None) -> None:
        model.status = status; model.archive_path = archive_path; model.error_message = error; model.processed_at = utcnow(); await self.session.flush()
