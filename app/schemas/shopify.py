from pydantic import BaseModel

class InventoryIdentity(BaseModel):
    sku: str
    variant_id: str | None = None
    inventory_item_id: str

class ShopifyWebhookOrderCreate(BaseModel):
    id: int | None = None
    admin_graphql_api_id: str | None = None

    @property
    def order_gid(self) -> str | None:
        if self.admin_graphql_api_id:
            return self.admin_graphql_api_id
        if self.id is not None:
            return f"gid://shopify/Order/{self.id}"
        return None
