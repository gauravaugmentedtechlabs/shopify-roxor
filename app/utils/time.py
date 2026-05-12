from datetime import UTC, datetime, timedelta
import random

def utcnow() -> datetime:
    """Timezone-aware UTC now."""
    return datetime.now(UTC)

def backoff_delay(attempts: int, base_seconds: int = 30, max_seconds: int = 3600) -> timedelta:
    """Return exponential backoff with small jitter."""
    seconds = min(max_seconds, base_seconds * (2 ** max(0, attempts))) + random.randint(0, 10)
    return timedelta(seconds=seconds)
