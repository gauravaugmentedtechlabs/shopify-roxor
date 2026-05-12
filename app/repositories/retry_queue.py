from typing import Any
from sqlalchemy import select
from app.models import ProcessingStatus, RetryQueue
from app.repositories.base import Repository
from app.utils.time import backoff_delay, utcnow

class RetryQueueRepository(Repository):
    """Retry queue repository with simple leasing semantics."""
    async def enqueue(self, *, operation_type: str, payload: dict[str, Any], correlation_id: str, error: str, max_attempts: int = 5) -> RetryQueue:
        model = RetryQueue(operation_type=operation_type, payload=payload, correlation_id=correlation_id, last_error=error, max_attempts=max_attempts, next_attempt_at=utcnow() + backoff_delay(0), status=ProcessingStatus.pending)
        self.session.add(model); await self.session.flush(); return model

    async def due(self, worker_id: str, limit: int = 25) -> list[RetryQueue]:
        stmt = select(RetryQueue).where(RetryQueue.status == ProcessingStatus.pending, RetryQueue.next_attempt_at <= utcnow()).order_by(RetryQueue.next_attempt_at).limit(limit).with_for_update(skip_locked=True)
        rows = list((await self.session.execute(stmt)).scalars())
        for row in rows:
            row.status = ProcessingStatus.processing; row.locked_at = utcnow(); row.locked_by = worker_id
        await self.session.flush(); return rows

    async def mark_success(self, row: RetryQueue) -> None:
        row.status = ProcessingStatus.succeeded; row.last_error = None; await self.session.flush()

    async def mark_failure(self, row: RetryQueue, error: str) -> None:
        row.attempts += 1; row.last_error = error; row.locked_at = None; row.locked_by = None
        if row.attempts >= row.max_attempts:
            row.status = ProcessingStatus.dead_letter
        else:
            row.status = ProcessingStatus.pending; row.next_attempt_at = utcnow() + backoff_delay(row.attempts)
        await self.session.flush()
