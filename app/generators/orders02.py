from datetime import UTC, datetime
from decimal import Decimal
from lxml import etree
from lxml.builder import E
from app.schemas.idoc import ShopifyOrderForXml

class Orders02Generator:
    """Generate SAP ORDERS02 IDOC XML using lxml builder semantics."""
    def generate(self, order: ShopifyOrderForXml) -> bytes:
        idoc = E.IDOC({"BEGIN": "1"}, self._control_record(), self._header(order), self._customer(order), *self._items(order))
        root = E.ORDERS02(idoc)
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")

    def _control_record(self):
        now = datetime.now(UTC)
        return E.EDI_DC40({"SEGMENT": "1"}, E.TABNAM("EDI_DC40"), E.DIRECT("2"), E.IDOCTYP("ORDERS02"), E.MESTYP("ORDERS"), E.CREDAT(now.strftime("%Y%m%d")), E.CRETIM(now.strftime("%H%M%S")))

    def _header(self, order: ShopifyOrderForXml):
        return E.E1EDK01({"SEGMENT": "1"}, E.BELNR(order.name), E.CURCY(order.currency_code), E.WKURS("1"), E.E1EDK02({"SEGMENT": "1"}, E.QUALF("001"), E.BELNR(order.id)))

    def _customer(self, order: ShopifyOrderForXml):
        return E.E1EDKA1({"SEGMENT": "1"}, E.PARVW("WE"), E.NAME1(order.shipping_name or order.customer_name or "Unknown"), E.STRAS(order.shipping_address1 or ""), E.ORT01(order.shipping_city or ""), E.PSTLZ(order.shipping_zip or ""), E.LAND1(order.shipping_country_code or ""))

    def _items(self, order: ShopifyOrderForXml):
        items = []
        for index, line in enumerate(order.lines, start=1):
            unit_price = Decimal(line.unit_price).quantize(Decimal("0.01"))
            items.append(E.E1EDP01({"SEGMENT": "1"}, E.POSEX(f"{index:06d}"), E.MENGE(str(line.quantity)), E.MENEE("EA"), E.E1EDP19({"SEGMENT": "1"}, E.QUALF("002"), E.IDTNR(line.sku)), E.E1EDP05({"SEGMENT": "1"}, E.KSCHL("NETP"), E.BETRG(str(unit_price)))))
        return items
