from sqlalchemy.ext.asyncio import AsyncSession
from app.parsers.invoice import InvoiceParser
from app.repositories import IntegrationLogRepository, OrderMappingRepository
from app.services.shopify import ShopifyService
from app.utils.exceptions import RetryableIntegrationError

class InvoiceProcessor:
    """Processes INVOIC02 files into DB state and Shopify metadata."""
    def __init__(self, session: AsyncSession, shopify: ShopifyService | None = None) -> None:
        self.session = session; self.shopify = shopify or ShopifyService(); self.orders = OrderMappingRepository(session); self.logs = IntegrationLogRepository(session)

    async def process(self, root, correlation_id: str) -> None:
        invoice = InvoiceParser().parse(root)
        mapping = await self.orders.by_reference(invoice.order_reference)
        if not mapping:
            raise RetryableIntegrationError(f"No order mapping found for invoice reference {invoice.order_reference}")
        await self.orders.attach_invoice(mapping, invoice.invoice_number, invoice.total, invoice.currency)
        await self.shopify.attach_invoice_metadata(mapping.shopify_order_id, invoice)
        await self.logs.add(correlation_id=correlation_id, event_type="invoice.attached", level="info", message="Invoice attached to Shopify order", context=invoice.model_dump(mode="json"))
