from pathlib import Path
from app.services.sftp.client import SftpClient

class SftpService:
    """Higher-level SFTP file service with reconnect-on-failure behavior."""
    def __init__(self, client: SftpClient | None = None) -> None:
        self.client = client or SftpClient()

    def list_files(self, remote_dir: str) -> list[str]:
        return self._with_reconnect(lambda: self.client.list_files(remote_dir))

    def download_file(self, remote_path: str, local_path: Path) -> Path:
        return self._with_reconnect(lambda: self.client.download_file(remote_path, local_path))

    def upload_bytes(self, payload: bytes, remote_path: str) -> None:
        self._with_reconnect(lambda: self.client.upload_bytes(payload, remote_path))

    def move_file(self, source: str, destination: str) -> None:
        self._with_reconnect(lambda: self.client.move_file(source, destination))

    def archive_file(self, source: str, destination: str) -> None:
        self.move_file(source, destination)

    def delete_file(self, remote_path: str) -> None:
        self._with_reconnect(lambda: self.client.delete_file(remote_path))

    def close(self) -> None:
        self.client.close()

    def _with_reconnect(self, func):
        try:
            return func()
        except Exception:
            self.client.reconnect()
            return func()
