from functools import lru_cache
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    app_env: str = Field("production", alias="APP_ENV")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    postgres_url: str = Field(..., alias="POSTGRES_URL")
    shopify_store: str = Field(..., alias="SHOPIFY_STORE")
    shopify_access_token: str = Field(..., alias="SHOPIFY_ACCESS_TOKEN")
    shopify_api_version: str = Field("2026-04", alias="SHOPIFY_API_VERSION")
    shopify_location_id: str = Field(..., alias="SHOPIFY_LOCATION_ID")
    shopify_webhook_secret: str = Field("", alias="SHOPIFY_WEBHOOK_SECRET")
    sftp_host: str = Field(..., alias="SFTP_HOST")
    sftp_port: int = Field(22, alias="SFTP_PORT")
    sftp_username: str = Field(..., alias="SFTP_USERNAME")
    sftp_password: str | None = Field(None, alias="SFTP_PASSWORD")
    sftp_private_key: str | None = Field(None, alias="SFTP_PRIVATE_KEY")
    sftp_private_key_passphrase: str | None = Field(None, alias="SFTP_PRIVATE_KEY_PASSPHRASE")
    sftp_outbound_orders_path: str = Field("/outbound/orders/", alias="SFTP_OUTBOUND_ORDERS_PATH")
    sftp_inbound_delivery_path: str = Field("/inbound/delivery/", alias="SFTP_INBOUND_DELIVERY_PATH")
    sftp_inbound_stock_path: str = Field("/inbound/stock/", alias="SFTP_INBOUND_STOCK_PATH")
    sftp_inbound_invoice_path: str = Field("/inbound/invoice/", alias="SFTP_INBOUND_INVOICE_PATH")
    sftp_archive_path: str = Field("/archive/", alias="SFTP_ARCHIVE_PATH")
    sftp_error_path: str = Field("/error/", alias="SFTP_ERROR_PATH")
    sftp_poll_interval_seconds: int = Field(30, alias="SFTP_POLL_INTERVAL_SECONDS")
    retry_worker_interval_seconds: int = Field(15, alias="RETRY_WORKER_INTERVAL_SECONDS")
    local_work_dir: Path = Field(Path("/tmp/shopify-roxor"), alias="LOCAL_WORK_DIR")
    workers_enabled: bool = Field(True, alias="WORKERS_ENABLED")

    @field_validator("shopify_store")
    @classmethod
    def normalize_store(cls, value: str) -> str:
        return value.replace("https://", "").replace("http://", "").rstrip("/")

    @property
    def shopify_graphql_url(self) -> str:
        return f"https://{self.shopify_store}/admin/api/{self.shopify_api_version}/graphql.json"

@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

settings = get_settings()
