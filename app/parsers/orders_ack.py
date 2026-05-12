from lxml import etree
from app.parsers.base import XmlParser
from app.services.xml.validator import first_text

class OrdersAckParser(XmlParser[str]):
    """Parse ORDERS02/ORDERS05 acknowledgement references."""
    def parse(self, root: etree._Element) -> str:
        return first_text(root, [".//E1EDK02/BELNR", ".//BELNR", ".//ORDER_REFERENCE"], "order acknowledgement reference")
