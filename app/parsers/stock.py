from lxml import etree
from app.parsers.base import XmlParser
from app.schemas.idoc import StockItem
from app.utils.exceptions import XmlValidationError

class StockParser(XmlParser[list[StockItem]]):
    """Parse Roxor stock XML into SKU absolute quantities."""
    def parse(self, root: etree._Element) -> list[StockItem]:
        items: dict[str, StockItem] = {}
        for node in root.xpath("//*[.//*[local-name()='SKU'] or .//*[local-name()='MATNR']]"):
            sku = self._first(node, [".//*[local-name()='SKU']/text()", ".//*[local-name()='MATNR']/text()"])
            quantity = self._first(node, [".//*[local-name()='QUANTITY']/text()", ".//*[local-name()='QTY']/text()", ".//*[local-name()='LABST']/text()"])
            if sku and quantity:
                normalized = sku.lstrip("0") or sku
                items[normalized] = StockItem(sku=normalized, quantity=int(float(quantity)))
        if not items:
            raise XmlValidationError("Stock XML contains no SKU/quantity rows")
        return list(items.values())

    def _first(self, node: etree._Element, xpaths: list[str]) -> str | None:
        for xpath in xpaths:
            values = node.xpath(xpath)
            if values and str(values[0]).strip():
                return str(values[0]).strip()
        return None
