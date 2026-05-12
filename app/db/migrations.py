from alembic import command
from alembic.config import Config


def upgrade_to_head(config_path: str = "alembic.ini") -> None:
    """Run Alembic migrations to the latest revision."""
    command.upgrade(Config(config_path), "head")
