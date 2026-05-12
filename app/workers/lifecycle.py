import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config.logging import logger
from app.config.settings import settings
from app.pollers.sftp_poller import SftpPoller
from app.workers.retry_worker import RetryWorker

log = logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan that starts background poller and retry worker."""
    tasks: list[asyncio.Task] = []
    poller = SftpPoller()
    retry_worker = RetryWorker()
    if settings.workers_enabled:
        tasks = [asyncio.create_task(poller.run_forever()), asyncio.create_task(retry_worker.run_forever())]
    try:
        yield
    finally:
        await poller.stop(); await retry_worker.stop()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        log.info("workers_stopped")
