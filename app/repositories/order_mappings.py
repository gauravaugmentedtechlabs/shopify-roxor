from decimal import Decimal
from sqlalchemy import select
from app.models import OrderMapping
from app.repositories.base import Repository

class OrderMappingRepository(Repository):
    """Order correlation repository."""
    async def by_shopify_id(self, shopify_order_id: str) -> OrderMapping | None:
        return (await self.session.execute(select(OrderMapping).where(OrderMapping.shopify_order_id == shopify_order_id))).scalar_one_or_none()

    async def by_reference(self, reference: str) -> OrderMapping | None:
        stmt = select(OrderMapping).where((OrderMapping.shopify_order_id == reference) | (OrderMapping.shopify_order_name == reference) | (OrderMapping.roxor_order_reference == reference))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def upsert_order(self, *, shopify_order_id: str, shopify_order_name: str, shopify_customer_id: str | None, status: str) -> OrderMapping:
        existing = await self.by_shopify_id(shopify_order_id)
        if existing:
            existing.shopify_order_name = shopify_order_name; existing.shopify_customer_id = shopify_customer_id; existing.status = status; await self.session.flush(); return existing
        model = OrderMapping(shopify_order_id=shopify_order_id, shopify_order_name=shopify_order_name, shopify_customer_id=shopify_customer_id, status=status)
        self.session.add(model); await self.session.flush(); return model

    async def attach_delivery(self, mapping: OrderMapping, delivery_reference: str) -> None:
        mapping.roxor_delivery_reference = delivery_reference; mapping.status = "fulfilled"; await self.session.flush()

    async def attach_invoice(self, mapping: OrderMapping, invoice_number: str, total: Decimal, currency: str | None) -> None:
        mapping.invoice_number = invoice_number; mapping.invoice_total = total; mapping.invoice_currency = currency; mapping.status = "invoiced"; await self.session.flush()
