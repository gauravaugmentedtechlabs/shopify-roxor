import asyncio
from pathlib import Path, PurePosixPath
from app.config.logging import logger
from app.config.settings import settings
from app.db.session import AsyncSessionLocal
from app.processors.inbound_dispatcher import InboundDispatcher
from app.services.sftp import SftpService

log = logger(__name__)

class SftpPoller:
    """Polls Roxor inbound SFTP folders for XML files every configured interval."""
    def __init__(self, sftp: SftpService | None = None) -> None:
        self.sftp = sftp or SftpService()
        self._running = False

    async def run_forever(self) -> None:
        self._running = True
        log.info("sftp_poller_started", interval=settings.sftp_poll_interval_seconds)
        while self._running:
            await self.poll_once()
            await asyncio.sleep(settings.sftp_poll_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        self.sftp.close()

    async def poll_once(self) -> int:
        """Poll all inbound folders once and process discovered XML files."""
        count = 0
        for remote_dir in (settings.sftp_inbound_delivery_path, settings.sftp_inbound_stock_path, settings.sftp_inbound_invoice_path):
            files = self.sftp.list_files(remote_dir)
            for remote_path in files:
                if self._skip(remote_path):
                    continue
                local_path = self._local_path(remote_path)
                self.sftp.download_file(remote_path, local_path)
                async with AsyncSessionLocal() as session:
                    await InboundDispatcher(session, self.sftp).process_remote_file(remote_path, local_path)
                count += 1
        if count:
            log.info("sftp_poll_processed", count=count)
        return count

    def _local_path(self, remote_path: str) -> Path:
        return settings.local_work_dir / "downloads" / PurePosixPath(remote_path).name

    def _skip(self, remote_path: str) -> bool:
        name = PurePosixPath(remote_path).name.lower()
        return name.startswith(".") or name.endswith((".tmp", ".part")) or not name.endswith(".xml")
