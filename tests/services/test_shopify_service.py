import pytest
from app.schemas.idoc import StockItem
from app.services.shopify.service import ShopifyService

class FakeGraphQLClient:
    def __init__(self): self.calls = []
    @staticmethod
    def idempotency_key(): return "idem"
    async def execute(self, query, variables=None, retries=3):
        self.calls.append((query, variables))
        if "productVariants" in query:
            return {"productVariants": {"edges": [{"node": {"id": "gid://shopify/ProductVariant/1", "sku": "ABC", "inventoryItem": {"id": "gid://shopify/InventoryItem/1"}}}]}}
        if "inventorySetQuantities" in query:
            return {"inventorySetQuantities": {"userErrors": [], "inventoryAdjustmentGroup": {"changes": []}}}
        raise AssertionError("unexpected query")

@pytest.mark.asyncio
async def test_update_inventory_finds_inventory_item_and_sets_quantity():
    client = FakeGraphQLClient()
    service = ShopifyService(client)  # type: ignore[arg-type]
    inventory_item_id = await service.update_inventory(StockItem(sku="ABC", quantity=4))
    assert inventory_item_id == "gid://shopify/InventoryItem/1"
    assert any("inventorySetQuantities" in call[0] for call in client.calls)
