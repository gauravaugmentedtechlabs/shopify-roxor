from lxml import etree
from app.parsers.base import XmlParser
from app.schemas.idoc import DeliveryConfirmation, DeliveryItem
from app.services.xml.validator import first_text
from app.utils.exceptions import XmlValidationError

class DeliveryParser(XmlParser[DeliveryConfirmation]):
    """Parse DELVRY07 delivery confirmation XML."""
    def parse(self, root: etree._Element) -> DeliveryConfirmation:
        order_reference = first_text(root, [".//E1EDL41[BSTNR]/BSTNR", ".//BSTNR", ".//ORDER_REFERENCE"], "order reference")
        delivery_number = root.findtext(".//VBELN") or root.findtext(".//DELIVERY_NUMBER") or order_reference
        tracking = first_text(root, [".//TRACKING_NUMBER", ".//TRACKN", ".//E1EDT13[QUALF='006']/NTANF", ".//EXIDV"], "tracking number")
        carrier = root.findtext(".//CARRIER") or root.findtext(".//ROUTE") or "Roxor"
        items: list[DeliveryItem] = []
        for node in root.xpath("//*[local-name()='E1EDL24' or local-name()='ITEM']"):
            sku = self._first(node, [".//MATNR/text()", ".//SKU/text()"])
            qty = self._first(node, [".//LFIMG/text()", ".//QUANTITY/text()", ".//QTY/text()"])
            if sku and qty:
                items.append(DeliveryItem(sku=sku.lstrip("0") or sku, quantity=int(float(qty))))
        if not items:
            raise XmlValidationError("DELVRY07 contains no shipped item rows")
        return DeliveryConfirmation(order_reference=order_reference, delivery_number=delivery_number.strip(), tracking_number=tracking, carrier=carrier.strip(), items=items)

    def _first(self, node: etree._Element, xpaths: list[str]) -> str | None:
        for xpath in xpaths:
            values = node.xpath(xpath)
            if values and str(values[0]).strip():
                return str(values[0]).strip()
        return None
