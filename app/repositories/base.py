from sqlalchemy.ext.asyncio import AsyncSession

class Repository:
    """Base repository with a shared async session."""
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
