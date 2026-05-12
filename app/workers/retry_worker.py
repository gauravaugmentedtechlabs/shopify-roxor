import asyncio
from pathlib import Path, PurePosixPath
from uuid import uuid4
from app.config.logging import logger
from app.config.settings import settings
from app.db.session import AsyncSessionLocal
from app.processors.inbound_dispatcher import InboundDispatcher
from app.processors.order_processor import OrderProcessor
from app.repositories import RetryQueueRepository
from app.services.sftp import SftpService

log = logger(__name__)

class RetryWorker:
    """Executes due retry queue items and dead-letters exhausted operations."""
    def __init__(self, worker_id: str | None = None, sftp: SftpService | None = None) -> None:
        self.worker_id = worker_id or str(uuid4())
        self.sftp = sftp or SftpService()
        self._running = False

    async def run_forever(self) -> None:
        self._running = True
        log.info("retry_worker_started", worker_id=self.worker_id)
        while self._running:
            await self.run_once()
            await asyncio.sleep(settings.retry_worker_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        self.sftp.close()

    async def run_once(self) -> int:
        async with AsyncSessionLocal() as session:
            repo = RetryQueueRepository(session)
            rows = await repo.due(self.worker_id)
            for row in rows:
                error: str | None = None
                try:
                    if row.operation_type == "shopify_order_created":
                        await OrderProcessor(session, sftp=self.sftp).process_order_created(row.payload["order_gid"], row.correlation_id)
                    elif row.operation_type == "process_remote_file":
                        remote_path = row.payload["remote_path"]
                        local_path = settings.local_work_dir / "retry" / PurePosixPath(remote_path).name
                        self.sftp.download_file(remote_path, local_path)
                        await InboundDispatcher(session, self.sftp).process_remote_file(remote_path, local_path)
                    else:
                        raise ValueError(f"Unsupported retry operation {row.operation_type}")
                except Exception as exc:
                    error = str(exc)
                    log.warning("retry_operation_failed", retry_id=row.id, operation=row.operation_type, error=error)
                if error:
                    await repo.mark_failure(row, error)
                else:
                    await repo.mark_success(row)
            await session.commit()
            return len(rows)
