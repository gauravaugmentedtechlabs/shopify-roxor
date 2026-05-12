from lxml import etree
from app.utils.exceptions import XmlValidationError

SUPPORTED_IDOC_TYPES = {"ORDERS02", "ORDERS05", "DELVRY07", "INVOIC02"}

def parse_xml(payload: bytes) -> etree._Element:
    """Parse XML bytes safely without external entities or network access."""
    try:
        parser = etree.XMLParser(resolve_entities=False, no_network=True, recover=False, remove_blank_text=True)
        return etree.fromstring(payload, parser)
    except etree.XMLSyntaxError as exc:
        raise XmlValidationError(f"Invalid XML syntax: {exc}") from exc

def detect_idoc_type(root: etree._Element) -> str:
    """Detect supported IDOC type from root or SAP control record fields."""
    candidates = [root.tag, root.findtext(".//IDOCTYP"), root.findtext(".//MESTYP"), root.findtext(".//STDMES")]
    text_sample = etree.tostring(root, encoding="unicode")[:4096]
    for candidate in candidates + [text_sample]:
        if not candidate:
            continue
        upper = candidate.upper()
        for idoc_type in SUPPORTED_IDOC_TYPES:
            if idoc_type in upper:
                return idoc_type
    if root.xpath("//*[local-name()='SKU']") and root.xpath("//*[local-name()='QUANTITY' or local-name()='QTY']"):
        return "STOCK"
    raise XmlValidationError("Unsupported or undetectable IDOC type")
