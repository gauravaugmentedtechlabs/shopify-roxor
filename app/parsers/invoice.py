from decimal import Decimal
from lxml import etree
from app.parsers.base import XmlParser
from app.schemas.idoc import Invoice
from app.services.xml.validator import first_text

class InvoiceParser(XmlParser[Invoice]):
    """Parse INVOIC02 invoice XML."""
    def parse(self, root: etree._Element) -> Invoice:
        invoice_number = first_text(root, [".//E1EDK01/BELNR", ".//INVOICE_NUMBER", ".//BELNR"], "invoice number")
        order_reference = first_text(root, [".//E1EDK02[QUALF='001']/BELNR", ".//ORDER_REFERENCE", ".//BSTNR"], "order reference")
        total = Decimal(first_text(root, [".//E1EDS01[SUMID='011']/SUMME", ".//TOTAL", ".//GROSS_TOTAL"], "invoice total"))
        currency = root.findtext(".//CURCY") or root.findtext(".//CURRENCY")
        return Invoice(order_reference=order_reference, invoice_number=invoice_number, total=total, currency=currency)
