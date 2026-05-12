import json
from decimal import Decimal
from app.config.settings import settings
from app.schemas.idoc import DeliveryConfirmation, Invoice, ShopifyOrderForXml, ShopifyOrderLine, StockItem
from app.schemas.shopify import InventoryIdentity
from app.services.shopify.client import ShopifyGraphQLClient
from app.services.shopify.mutations import FULFILLMENT_CREATE_MUTATION, INVENTORY_SET_QUANTITIES_MUTATION, METAFIELDS_SET_MUTATION
from app.services.shopify.queries import ORDER_QUERY, ORDER_SEARCH_QUERY, VARIANT_BY_SKU_QUERY
from app.utils.exceptions import ShopifyApiError

class ShopifyService:
    """High-level Shopify Admin API operations for the integration."""
    def __init__(self, client: ShopifyGraphQLClient | None = None) -> None:
        self.client = client or ShopifyGraphQLClient()

    async def fetch_complete_order(self, order_gid: str) -> ShopifyOrderForXml:
        """Fetch a complete Shopify order and convert it to the XML generator schema."""
        cursor: str | None = None
        order_data: dict | None = None
        lines: list[ShopifyOrderLine] = []
        while True:
            data = await self.client.execute(ORDER_QUERY, {"id": order_gid, "cursor": cursor})
            order = data.get("order")
            if not order:
                raise ShopifyApiError(f"Order not found: {order_gid}")
            order_data = order
            for edge in order["lineItems"]["edges"]:
                node = edge["node"]
                sku = node.get("sku") or (node.get("variant") or {}).get("sku")
                if not sku:
                    raise ShopifyApiError(f"Order {order_gid} contains a line without SKU")
                amount = ((node.get("discountedUnitPriceSet") or {}).get("shopMoney") or {}).get("amount") or "0.00"
                lines.append(ShopifyOrderLine(sku=sku, quantity=int(node.get("quantity") or 0), unit_price=Decimal(amount)))
            page = order["lineItems"]["pageInfo"]
            if not page.get("hasNextPage"):
                break
            cursor = page.get("endCursor")
        assert order_data is not None
        shipping = order_data.get("shippingAddress") or {}
        customer = order_data.get("customer") or {}
        return ShopifyOrderForXml(id=order_data["id"], name=order_data["name"], currency_code=order_data.get("currencyCode") or "GBP", customer_name=customer.get("displayName"), customer_email=customer.get("email"), shipping_name=shipping.get("name"), shipping_address1=shipping.get("address1"), shipping_city=shipping.get("city"), shipping_zip=shipping.get("zip"), shipping_country_code=shipping.get("countryCodeV2"), lines=lines)

    async def find_order_by_reference(self, reference: str) -> dict:
        """Find a Shopify order by name/reference for delivery or invoice processing."""
        data = await self.client.execute(ORDER_SEARCH_QUERY, {"query": f"name:{reference}"})
        edges = data.get("orders", {}).get("edges", [])
        if not edges:
            raise ShopifyApiError(f"Shopify order not found for reference {reference}")
        return edges[0]["node"]

    async def find_inventory_identity_by_sku(self, sku: str) -> InventoryIdentity:
        """Find Shopify inventory item identity by SKU."""
        data = await self.client.execute(VARIANT_BY_SKU_QUERY, {"query": f"sku:{sku}"})
        edges = data.get("productVariants", {}).get("edges", [])
        if not edges:
            raise ShopifyApiError(f"SKU not found in Shopify: {sku}")
        node = edges[0]["node"]
        return InventoryIdentity(sku=node["sku"], variant_id=node.get("id"), inventory_item_id=node["inventoryItem"]["id"])

    async def update_inventory(self, item: StockItem, inventory_item_id: str | None = None) -> str:
        """Set absolute Shopify inventory quantity for a SKU at the configured location."""
        identity_id = inventory_item_id or (await self.find_inventory_identity_by_sku(item.sku)).inventory_item_id
        variables = {"idempotencyKey": self.client.idempotency_key(), "input": {"name": "available", "reason": "correction", "ignoreCompareQuantity": True, "referenceDocumentUri": f"gid://roxor-erp/StockUpdate/{item.sku}", "quantities": [{"inventoryItemId": identity_id, "locationId": settings.shopify_location_id, "quantity": item.quantity, "compareQuantity": None}]}}
        data = await self.client.execute(INVENTORY_SET_QUANTITIES_MUTATION, variables)
        self._raise_user_errors(data["inventorySetQuantities"].get("userErrors", []))
        return identity_id

    async def create_fulfillment(self, confirmation: DeliveryConfirmation, shopify_order: dict | None = None) -> None:
        """Create a Shopify fulfillment with carrier and tracking number."""
        order = shopify_order or await self.find_order_by_reference(confirmation.order_reference)
        fulfillment_orders = [edge["node"] for edge in order.get("fulfillmentOrders", {}).get("edges", []) if edge["node"].get("status") not in {"CLOSED", "CANCELLED"}]
        if not fulfillment_orders:
            raise ShopifyApiError(f"No open fulfillment orders for {confirmation.order_reference}")
        variables = {"fulfillment": {"notifyCustomer": True, "trackingInfo": {"number": confirmation.tracking_number, "company": confirmation.carrier}, "lineItemsByFulfillmentOrder": [{"fulfillmentOrderId": fulfillment_orders[0]["id"]}]}}
        data = await self.client.execute(FULFILLMENT_CREATE_MUTATION, variables)
        self._raise_user_errors(data["fulfillmentCreate"].get("userErrors", []))

    async def attach_invoice_metadata(self, shopify_order_id: str, invoice: Invoice) -> None:
        """Attach Roxor invoice details as a Shopify order metafield."""
        variables = {"metafields": [{"ownerId": shopify_order_id, "namespace": "roxor", "key": "invoice", "type": "json", "value": json.dumps({"invoice_number": invoice.invoice_number, "total": str(invoice.total), "currency": invoice.currency})}]}
        data = await self.client.execute(METAFIELDS_SET_MUTATION, variables)
        self._raise_user_errors(data["metafieldsSet"].get("userErrors", []))

    def _raise_user_errors(self, errors: list[dict]) -> None:
        if errors:
            raise ShopifyApiError(f"Shopify user errors: {errors}")
