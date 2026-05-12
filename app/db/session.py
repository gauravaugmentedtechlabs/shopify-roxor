from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config.settings import settings

engine_kwargs: dict[str, object] = {"pool_pre_ping": True}
if not settings.postgres_url.startswith("sqlite"):
    engine_kwargs.update({"pool_size": 5, "max_overflow": 10})
engine = create_async_engine(settings.postgres_url, **engine_kwargs)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        yield session
