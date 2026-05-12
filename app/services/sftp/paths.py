from datetime import UTC, datetime
from pathlib import PurePosixPath
from app.config.settings import settings

class SftpPaths:
    """Resolved remote SFTP folder layout."""
    outbound_orders = settings.sftp_outbound_orders_path
    inbound_delivery = settings.sftp_inbound_delivery_path
    inbound_stock = settings.sftp_inbound_stock_path
    inbound_invoice = settings.sftp_inbound_invoice_path
    archive = settings.sftp_archive_path
    error = settings.sftp_error_path

    @staticmethod
    def archive_for(filename: str) -> str:
        today = datetime.now(UTC)
        return str(PurePosixPath(settings.sftp_archive_path) / f"{today:%Y}" / f"{today:%m}" / f"{today:%d}" / filename)

    @staticmethod
    def error_for(filename: str) -> str:
        today = datetime.now(UTC)
        return str(PurePosixPath(settings.sftp_error_path) / f"{today:%Y}" / f"{today:%m}" / f"{today:%d}" / filename)
