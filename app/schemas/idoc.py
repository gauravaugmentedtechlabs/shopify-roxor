from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class StockItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    sku: str
    quantity: int

class DeliveryItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    sku: str
    quantity: int

class DeliveryConfirmation(BaseModel):
    model_config = ConfigDict(frozen=True)
    order_reference: str
    delivery_number: str
    tracking_number: str
    carrier: str
    items: list[DeliveryItem]

class Invoice(BaseModel):
    model_config = ConfigDict(frozen=True)
    order_reference: str
    invoice_number: str
    total: Decimal
    currency: str | None = None

class ShopifyOrderLine(BaseModel):
    sku: str
    quantity: int
    unit_price: Decimal = Decimal("0.00")

class ShopifyOrderForXml(BaseModel):
    id: str
    name: str
    currency_code: str = Field(default="GBP")
    customer_name: str | None = None
    customer_email: str | None = None
    shipping_name: str | None = None
    shipping_address1: str | None = None
    shipping_city: str | None = None
    shipping_zip: str | None = None
    shipping_country_code: str | None = None
    lines: list[ShopifyOrderLine]
