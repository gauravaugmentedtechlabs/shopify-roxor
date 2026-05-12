from pathlib import PurePosixPath
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.logging import logger
from app.config.settings import settings
from app.generators.orders02 import Orders02Generator
from app.models import FileDirection, ProcessingStatus
from app.repositories import IntegrationLogRepository, OrderMappingRepository, ProcessedFileRepository, RetryQueueRepository
from app.services.sftp import SftpService
from app.services.shopify import ShopifyService
from app.utils.hashing import sha256_bytes
from app.utils.time import utcnow

log = logger(__name__)

class OrderProcessor:
    """Processes Shopify order webhooks into ORDERS02 SFTP uploads."""
    def __init__(self, session: AsyncSession, shopify: ShopifyService | None = None, sftp: SftpService | None = None) -> None:
        self.session = session; self.shopify = shopify or ShopifyService(); self.sftp = sftp or SftpService()
        self.orders = OrderMappingRepository(session); self.files = ProcessedFileRepository(session); self.logs = IntegrationLogRepository(session); self.retries = RetryQueueRepository(session)

    async def process_order_created(self, order_gid: str, correlation_id: str | None = None) -> str:
        correlation_id = correlation_id or str(uuid4())
        try:
            existing = await self.orders.by_shopify_id(order_gid)
            if existing and existing.status == "sent_to_roxor":
                await self.logs.add(correlation_id=correlation_id, event_type="order.duplicate", level="info", message="Duplicate order webhook ignored", context={"order_gid": order_gid})
                await self.session.commit(); return correlation_id
            order = await self.shopify.fetch_complete_order(order_gid)
            xml_bytes = Orders02Generator().generate(order)
            filename = f"ORDERS02_{order.name.replace('#', '')}_{correlation_id}.xml"
            remote_path = str(PurePosixPath(settings.sftp_outbound_orders_path) / filename)
            self.sftp.upload_bytes(xml_bytes, remote_path)
            await self.orders.upsert_order(shopify_order_id=order.id, shopify_order_name=order.name, shopify_customer_id=None, status="sent_to_roxor")
            await self.files.create(filename=filename, remote_path=remote_path, file_hash=sha256_bytes(xml_bytes), idoc_type="ORDERS02", direction=FileDirection.outbound_to_roxor, correlation_id=correlation_id, status=ProcessingStatus.processed)
            await self.logs.add(correlation_id=correlation_id, event_type="order.uploaded", level="info", message="ORDERS02 uploaded to SFTP", context={"remote_path": remote_path})
            await self.session.commit(); return correlation_id
        except Exception as exc:
            await self.session.rollback()
            async with self.session.begin():
                await self.retries.enqueue(operation_type="shopify_order_created", payload={"order_gid": order_gid}, correlation_id=correlation_id, error=str(exc))
            log.exception("order_processing_failed", order_gid=order_gid, correlation_id=correlation_id)
            raise
