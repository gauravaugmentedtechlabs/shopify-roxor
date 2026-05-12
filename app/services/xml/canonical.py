from lxml import etree

def canonical_bytes(root: etree._Element) -> bytes:
    """Return canonical XML bytes for deterministic comparisons."""
    return etree.tostring(root, method="c14n")
