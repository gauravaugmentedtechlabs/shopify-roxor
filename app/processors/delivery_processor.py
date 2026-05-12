from sqlalchemy.ext.asyncio import AsyncSession
from app.parsers.delivery import DeliveryParser
from app.repositories import IntegrationLogRepository, OrderMappingRepository
from app.services.shopify import ShopifyService

class DeliveryProcessor:
    """Processes DELVRY07 files into Shopify fulfillments."""
    def __init__(self, session: AsyncSession, shopify: ShopifyService | None = None) -> None:
        self.session = session; self.shopify = shopify or ShopifyService(); self.orders = OrderMappingRepository(session); self.logs = IntegrationLogRepository(session)

    async def process(self, root, correlation_id: str) -> None:
        confirmation = DeliveryParser().parse(root)
        mapping = await self.orders.by_reference(confirmation.order_reference)
        shopify_order = None
        if mapping:
            shopify_order = await self.shopify.find_order_by_reference(mapping.shopify_order_name)
        await self.shopify.create_fulfillment(confirmation, shopify_order)
        if mapping:
            await self.orders.attach_delivery(mapping, confirmation.delivery_number)
        await self.logs.add(correlation_id=correlation_id, event_type="delivery.fulfilled", level="info", message="Delivery confirmation fulfilled in Shopify", context=confirmation.model_dump())
