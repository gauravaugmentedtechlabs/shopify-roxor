from decimal import Decimal
from app.generators.orders02 import Orders02Generator
from app.schemas.idoc import ShopifyOrderForXml, ShopifyOrderLine


def test_orders02_generator_maps_order_customer_and_sku():
    order = ShopifyOrderForXml(id="gid://shopify/Order/1", name="#1001", currency_code="GBP", shipping_name="Jane Buyer", lines=[ShopifyOrderLine(sku="SKU-1", quantity=3, unit_price=Decimal("9.99"))])
    xml = Orders02Generator().generate(order)
    assert b"<IDOCTYP>ORDERS02</IDOCTYP>" in xml
    assert b"<BELNR>#1001</BELNR>" in xml
    assert b"<NAME1>Jane Buyer</NAME1>" in xml
    assert b"<IDTNR>SKU-1</IDTNR>" in xml
    assert b"<MENGE>3</MENGE>" in xml
