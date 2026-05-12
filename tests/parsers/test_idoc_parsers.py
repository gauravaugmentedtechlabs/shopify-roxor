from decimal import Decimal
from app.parsers.delivery import DeliveryParser
from app.parsers.invoice import InvoiceParser
from app.parsers.stock import StockParser
from app.services.xml.detector import detect_idoc_type, parse_xml


def test_delivery_parser_extracts_tracking_carrier_delivery_and_items():
    root = parse_xml(b"<DELVRY07><BSTNR>#1001</BSTNR><VBELN>D1</VBELN><TRACKING_NUMBER>T1</TRACKING_NUMBER><CARRIER>DHL</CARRIER><ITEM><SKU>ABC</SKU><QUANTITY>2</QUANTITY></ITEM></DELVRY07>")
    parsed = DeliveryParser().parse(root)
    assert parsed.delivery_number == "D1"
    assert parsed.tracking_number == "T1"
    assert parsed.items[0].sku == "ABC"


def test_stock_parser_extracts_sku_quantity():
    root = parse_xml(b"<STOCK><ITEM><SKU>ABC</SKU><QUANTITY>7</QUANTITY></ITEM></STOCK>")
    parsed = StockParser().parse(root)
    assert parsed[0].sku == "ABC"
    assert parsed[0].quantity == 7


def test_invoice_parser_extracts_invoice_fields():
    root = parse_xml(b"<INVOIC02><INVOICE_NUMBER>I1</INVOICE_NUMBER><ORDER_REFERENCE>#1001</ORDER_REFERENCE><TOTAL>10.50</TOTAL><CURRENCY>GBP</CURRENCY></INVOIC02>")
    invoice = InvoiceParser().parse(root)
    assert invoice.invoice_number == "I1"
    assert invoice.total == Decimal("10.50")


def test_detect_supported_idoc_type():
    assert detect_idoc_type(parse_xml(b"<ORDERS05><IDOC/></ORDERS05>")) == "ORDERS05"
