from decimal import Decimal
from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin

class OrderMapping(TimestampMixin, Base):
    """Correlates Shopify order IDs with Roxor/SAP references."""
    __tablename__ = "order_mappings"
    id: Mapped[int] = mapped_column(primary_key=True)
    shopify_order_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    shopify_order_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    shopify_customer_id: Mapped[str | None] = mapped_column(String(128))
    roxor_order_reference: Mapped[str | None] = mapped_column(String(128), index=True)
    roxor_delivery_reference: Mapped[str | None] = mapped_column(String(128))
    invoice_number: Mapped[str | None] = mapped_column(String(128), index=True)
    invoice_total: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    invoice_currency: Mapped[str | None] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(64), default="created", nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
