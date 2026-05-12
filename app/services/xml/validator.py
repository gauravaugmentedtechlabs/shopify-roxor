from lxml import etree
from app.utils.exceptions import XmlValidationError

def first_text(root: etree._Element, xpaths: list[str], field_name: str) -> str:
    """Return the first non-empty text for any XPath, or raise validation error."""
    for xpath in xpaths:
        value = root.findtext(xpath)
        if value and value.strip():
            return value.strip()
    raise XmlValidationError(f"Missing required XML field: {field_name}")
