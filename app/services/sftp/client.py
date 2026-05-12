from io import StringIO
from pathlib import Path, PurePosixPath
import socket
import paramiko
from app.config.logging import logger
from app.config.settings import settings
from app.utils.exceptions import SftpError

log = logger(__name__)

class SftpClient:
    """Paramiko SFTP client supporting password and private-key authentication."""
    def __init__(self) -> None:
        self._ssh: paramiko.SSHClient | None = None
        self._sftp: paramiko.SFTPClient | None = None

    def connect(self) -> None:
        """Open SSH and SFTP sessions."""
        self.close()
        try:
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.RejectPolicy())
            pkey = self._load_private_key(settings.sftp_private_key) if settings.sftp_private_key else None
            ssh.connect(hostname=settings.sftp_host, port=settings.sftp_port, username=settings.sftp_username, password=settings.sftp_password or None, pkey=pkey, timeout=30, banner_timeout=30, auth_timeout=30)
            self._ssh = ssh; self._sftp = ssh.open_sftp()
            log.info("sftp_connected", host=settings.sftp_host, port=settings.sftp_port)
        except (paramiko.SSHException, socket.error, OSError) as exc:
            self.close()
            raise SftpError(f"Failed to connect to SFTP: {exc}") from exc

    def reconnect(self) -> None:
        """Reconnect the SSH/SFTP session."""
        log.warning("sftp_reconnecting")
        self.connect()

    def close(self) -> None:
        """Close SFTP and SSH sessions."""
        if self._sftp:
            self._sftp.close()
        if self._ssh:
            self._ssh.close()
        self._sftp = None; self._ssh = None

    def list_files(self, remote_dir: str) -> list[str]:
        sftp = self._ensure()
        try:
            return [str(PurePosixPath(remote_dir) / attr.filename) for attr in sftp.listdir_attr(remote_dir) if not attr.filename.startswith(".") and attr.filename.lower().endswith(".xml")]
        except OSError as exc:
            raise SftpError(f"Failed to list {remote_dir}: {exc}") from exc

    def download_file(self, remote_path: str, local_path: Path) -> Path:
        sftp = self._ensure(); local_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            sftp.get(remote_path, str(local_path)); log.info("sftp_downloaded", remote_path=remote_path, local_path=str(local_path)); return local_path
        except OSError as exc:
            raise SftpError(f"Failed to download {remote_path}: {exc}") from exc

    def upload_file(self, local_path: Path, remote_path: str) -> None:
        sftp = self._ensure(); self._mkdir_parent(remote_path)
        tmp_remote = f"{remote_path}.part"
        try:
            sftp.put(str(local_path), tmp_remote); sftp.rename(tmp_remote, remote_path); log.info("sftp_uploaded", remote_path=remote_path)
        except OSError as exc:
            raise SftpError(f"Failed to upload {remote_path}: {exc}") from exc

    def upload_bytes(self, payload: bytes, remote_path: str) -> None:
        local = settings.local_work_dir / "uploads" / PurePosixPath(remote_path).name
        local.parent.mkdir(parents=True, exist_ok=True); local.write_bytes(payload); self.upload_file(local, remote_path)

    def move_file(self, source: str, destination: str) -> None:
        sftp = self._ensure(); self._mkdir_parent(destination)
        try:
            sftp.rename(source, destination); log.info("sftp_moved", source=source, destination=destination)
        except OSError as exc:
            raise SftpError(f"Failed to move {source} to {destination}: {exc}") from exc

    def archive_file(self, source: str, destination: str) -> None:
        self.move_file(source, destination)

    def delete_file(self, remote_path: str) -> None:
        try:
            self._ensure().remove(remote_path); log.info("sftp_deleted", remote_path=remote_path)
        except OSError as exc:
            raise SftpError(f"Failed to delete {remote_path}: {exc}") from exc

    def _ensure(self) -> paramiko.SFTPClient:
        if self._sftp is None:
            self.connect()
        assert self._sftp is not None
        return self._sftp

    def _mkdir_parent(self, remote_path: str) -> None:
        sftp = self._ensure(); parent = PurePosixPath(remote_path).parent
        current = PurePosixPath("/")
        for part in parent.parts:
            if part == "/":
                continue
            current /= part
            try:
                sftp.stat(str(current))
            except OSError:
                sftp.mkdir(str(current))

    def _load_private_key(self, value: str | None) -> paramiko.PKey | None:
        if not value:
            return None
        loaders = (paramiko.RSAKey.from_private_key, paramiko.Ed25519Key.from_private_key, paramiko.ECDSAKey.from_private_key)
        key_text = Path(value).read_text() if Path(value).exists() else value
        last: Exception | None = None
        for loader in loaders:
            try:
                return loader(StringIO(key_text))
            except Exception as exc:  # Paramiko raises several key-specific exceptions.
                last = exc
        raise SftpError(f"Unable to load SFTP private key: {last}")
