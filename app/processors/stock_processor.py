from sqlalchemy.ext.asyncio import AsyncSession
from app.config.settings import settings
from app.parsers.stock import StockParser
from app.repositories import IntegrationLogRepository, InventoryMappingRepository
from app.services.shopify import ShopifyService

class StockProcessor:
    """Processes stock XML into Shopify absolute inventory updates."""
    def __init__(self, session: AsyncSession, shopify: ShopifyService | None = None) -> None:
        self.session = session; self.shopify = shopify or ShopifyService(); self.inventory = InventoryMappingRepository(session); self.logs = IntegrationLogRepository(session)

    async def process(self, root, correlation_id: str) -> None:
        for item in StockParser().parse(root):
            mapping = await self.inventory.by_sku_location(item.sku, settings.shopify_location_id)
            if mapping:
                inventory_item_id = mapping.shopify_inventory_item_id; variant_id = mapping.shopify_variant_id
            else:
                identity = await self.shopify.find_inventory_identity_by_sku(item.sku)
                inventory_item_id = identity.inventory_item_id; variant_id = identity.variant_id
            await self.shopify.update_inventory(item, inventory_item_id)
            await self.inventory.upsert(sku=item.sku, location_id=settings.shopify_location_id, inventory_item_id=inventory_item_id, variant_id=variant_id, quantity=item.quantity)
        await self.logs.add(correlation_id=correlation_id, event_type="stock.updated", level="info", message="Stock update processed")
