from sqlalchemy import select
from app.models import InventoryMapping
from app.repositories.base import Repository
from app.utils.time import utcnow

class InventoryMappingRepository(Repository):
    """Repository for SKU-to-Shopify inventory mappings."""
    async def by_sku_location(self, sku: str, location_id: str) -> InventoryMapping | None:
        stmt = select(InventoryMapping).where(InventoryMapping.sku == sku, InventoryMapping.shopify_location_id == location_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def upsert(self, *, sku: str, location_id: str, inventory_item_id: str, variant_id: str | None = None, quantity: int | None = None) -> InventoryMapping:
        existing = await self.by_sku_location(sku, location_id)
        if existing:
            existing.shopify_inventory_item_id = inventory_item_id; existing.shopify_variant_id = variant_id or existing.shopify_variant_id
            if quantity is not None: existing.last_known_quantity = quantity; existing.last_synced_at = utcnow()
            await self.session.flush(); return existing
        model = InventoryMapping(sku=sku, shopify_location_id=location_id, shopify_inventory_item_id=inventory_item_id, shopify_variant_id=variant_id, last_known_quantity=quantity, last_synced_at=utcnow() if quantity is not None else None)
        self.session.add(model); await self.session.flush(); return model
