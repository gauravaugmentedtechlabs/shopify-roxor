from typing import Any
from app.models import IntegrationLog
from app.repositories.base import Repository

class IntegrationLogRepository(Repository):
    """Durable audit-log repository."""
    async def add(self, *, correlation_id: str, event_type: str, level: str, message: str, context: dict[str, Any] | None = None, duration_ms: int | None = None) -> None:
        self.session.add(IntegrationLog(correlation_id=correlation_id, event_type=event_type, level=level, message=message, context=context or {}, duration_ms=duration_ms))
        await self.session.flush()
