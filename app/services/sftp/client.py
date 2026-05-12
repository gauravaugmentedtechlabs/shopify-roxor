from io import StringIO
from pathlib import Path, PurePosixPath
import os
import shutil
import socket
import subprocess
import tempfile
import paramiko
from app.config.logging import logger
from app.config.settings import settings
from app.utils.exceptions import SftpError

log = logger(__name__)

class SftpClient:
    """Paramiko SFTP client supporting password, OpenSSH key, and PuTTY PPK key authentication."""
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
            log.info("sftp_connected", host=settings.sftp_host, port=settings.sftp_port, key_auth=bool(pkey))
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
        """Load OpenSSH or PuTTY PPK private keys from a path or raw key text.

        Paramiko is tried first because recent releases can parse multiple key
        formats directly. If the key is a PuTTY PPK and Paramiko cannot parse it,
        the method falls back to `puttygen` conversion to an OpenSSH PEM key. The
        Docker image installs `putty-tools` for this fallback.
        """
        if not value:
            return None
        source_path = Path(value).expanduser()
        key_text = source_path.read_text() if source_path.exists() else value
        passphrase = settings.sftp_private_key_passphrase or None
        direct_key = self._try_paramiko_key_loaders(key_text, passphrase)
        if direct_key:
            return direct_key
        if self._is_putty_ppk(key_text):
            converted = self._convert_ppk_to_openssh(key_text, passphrase)
            converted_key = self._try_paramiko_key_loaders(converted, passphrase)
            if converted_key:
                return converted_key
        raise SftpError("Unable to load SFTP private key. For PuTTY .ppk files, provide a supported PPK/OpenSSH key and SFTP_PRIVATE_KEY_PASSPHRASE if encrypted.")

    def _try_paramiko_key_loaders(self, key_text: str, passphrase: str | None) -> paramiko.PKey | None:
        loaders = (paramiko.RSAKey.from_private_key, paramiko.Ed25519Key.from_private_key, paramiko.ECDSAKey.from_private_key, paramiko.DSSKey.from_private_key)
        last: Exception | None = None
        for loader in loaders:
            try:
                return loader(StringIO(key_text), password=passphrase)
            except Exception as exc:
                last = exc
        log.debug("sftp_key_loader_failed", error=str(last) if last else None)
        return None

    def _is_putty_ppk(self, key_text: str) -> bool:
        return key_text.lstrip().startswith("PuTTY-User-Key-File-")

    def _convert_ppk_to_openssh(self, key_text: str, passphrase: str | None) -> str:
        puttygen = shutil.which("puttygen")
        if not puttygen:
            raise SftpError("PuTTY .ppk key detected but puttygen is not installed. Install putty-tools or export the key in OpenSSH format.")
        with tempfile.TemporaryDirectory(prefix="roxor-ppk-") as tmp:
            tmp_path = Path(tmp)
            ppk_path = tmp_path / "key.ppk"
            out_path = tmp_path / "key.openssh"
            ppk_path.write_text(key_text)
            os.chmod(ppk_path, 0o600)
            cmd = [puttygen, str(ppk_path), "-O", "private-openssh", "-o", str(out_path)]
            passphrase_file: Path | None = None
            if passphrase:
                passphrase_file = tmp_path / "passphrase.txt"
                passphrase_file.write_text(passphrase)
                os.chmod(passphrase_file, 0o600)
                cmd.extend(["--old-passphrase", str(passphrase_file)])
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            if result.returncode != 0:
                raise SftpError(f"puttygen failed to convert PPK key: {result.stderr.strip() or result.stdout.strip()}")
            return out_path.read_text()
