from datetime import datetime
from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin

class InventoryMapping(TimestampMixin, Base):
    """Caches Shopify inventory identifiers for Roxor SKUs."""
    __tablename__ = "inventory_mappings"
    __table_args__ = (UniqueConstraint("sku", "shopify_location_id", name="uq_inventory_sku_location"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(255), nullable=False)
    shopify_variant_id: Mapped[str | None] = mapped_column(String(128))
    shopify_inventory_item_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    shopify_location_id: Mapped[str] = mapped_column(String(128), nullable=False)
    last_known_quantity: Mapped[int | None] = mapped_column(Integer)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
