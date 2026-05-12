from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.workers.retry_worker import RetryWorker

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/retries/run-once")
async def run_retries_once(session: AsyncSession = Depends(get_session)) -> dict[str, int]:
    """Operational endpoint to execute retry worker once."""
    count = await RetryWorker().run_once()
    return {"processed": count}
