class IntegrationError(Exception):
    """Base integration exception."""
    retryable = False

class RetryableIntegrationError(IntegrationError):
    """Transient exception suitable for retry queue scheduling."""
    retryable = True

class NonRetryableIntegrationError(IntegrationError):
    """Permanent exception that should be dead-lettered."""

class XmlValidationError(NonRetryableIntegrationError):
    """Invalid or unsupported XML payload."""

class ShopifyApiError(RetryableIntegrationError):
    """Shopify API request failed."""

class SftpError(RetryableIntegrationError):
    """SFTP request failed."""
