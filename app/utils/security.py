import base64
import hashlib
import hmac

def verify_shopify_hmac(raw_body: bytes, secret: str, hmac_header: str | None) -> bool:
    """Validate Shopify webhook HMAC-SHA256."""
    if not secret:
        return True
    if not hmac_header:
        return False
    digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, hmac_header)
