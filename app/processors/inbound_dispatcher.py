from pathlib import Path, PurePosixPath
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.logging import logger
from app.models import FileDirection, ProcessingStatus
from app.parsers.orders_ack import OrdersAckParser
from app.processors.delivery_processor import DeliveryProcessor
from app.processors.invoice_processor import InvoiceProcessor
from app.processors.stock_processor import StockProcessor
from app.repositories import IntegrationLogRepository, OrderMappingRepository, ProcessedFileRepository, RetryQueueRepository
from app.services.sftp.paths import SftpPaths
from app.services.sftp.service import SftpService
from app.services.xml.detector import detect_idoc_type, parse_xml
from app.utils.hashing import sha256_bytes
from app.utils.time import utcnow

log = logger(__name__)

class InboundDispatcher:
    """Dispatches downloaded Roxor XML files to the correct business processor."""
    def __init__(self, session: AsyncSession, sftp: SftpService | None = None) -> None:
        self.session = session; self.sftp = sftp or SftpService(); self.files = ProcessedFileRepository(session); self.logs = IntegrationLogRepository(session); self.retries = RetryQueueRepository(session); self.orders = OrderMappingRepository(session)

    async def process_remote_file(self, remote_path: str, local_path: Path) -> None:
        payload = local_path.read_bytes(); file_hash = sha256_bytes(payload); correlation_id = file_hash[:16]
        filename = PurePosixPath(remote_path).name
        duplicate = await self.files.by_hash(file_hash)
        if duplicate:
            archive_path = SftpPaths.archive_for(filename)
            self.sftp.archive_file(remote_path, archive_path)
            await self.logs.add(correlation_id=correlation_id, event_type="file.duplicate", level="info", message="Duplicate file archived", context={"remote_path": remote_path})
            await self.session.commit(); return
        try:
            root = parse_xml(payload); idoc_type = detect_idoc_type(root)
            file_row = await self.files.create(filename=filename, remote_path=remote_path, file_hash=file_hash, idoc_type=idoc_type, direction=FileDirection.inbound_from_roxor, correlation_id=correlation_id)
            if idoc_type == "DELVRY07":
                await DeliveryProcessor(self.session).process(root, correlation_id)
            elif idoc_type == "INVOIC02":
                await InvoiceProcessor(self.session).process(root, correlation_id)
            elif idoc_type == "STOCK":
                await StockProcessor(self.session).process(root, correlation_id)
            elif idoc_type in {"ORDERS02", "ORDERS05"}:
                reference = OrdersAckParser().parse(root); mapping = await self.orders.by_reference(reference)
                if mapping:
                    mapping.status = "acknowledged"
            archive_path = SftpPaths.archive_for(filename)
            self.sftp.archive_file(remote_path, archive_path)
            await self.files.mark_complete(file_row, ProcessingStatus.processed, archive_path=archive_path)
            await self.logs.add(correlation_id=correlation_id, event_type="file.processed", level="info", message="Inbound XML processed", context={"idoc_type": idoc_type, "remote_path": remote_path})
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            error_path = SftpPaths.error_for(filename)
            self.sftp.move_file(remote_path, error_path)
            async with self.session.begin():
                await self.files.create(filename=filename, remote_path=remote_path, file_hash=file_hash, idoc_type="unknown", direction=FileDirection.inbound_from_roxor, correlation_id=correlation_id, status=ProcessingStatus.failed)
                await self.retries.enqueue(operation_type="process_remote_file", payload={"remote_path": error_path}, correlation_id=correlation_id, error=str(exc))
            log.exception("inbound_file_failed", remote_path=remote_path, correlation_id=correlation_id)
            raise
