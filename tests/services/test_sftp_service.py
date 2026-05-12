from pathlib import Path
from app.services.sftp.service import SftpService

class FakeClient:
    def __init__(self):
        self.files = ["/inbound/stock/a.xml"]
        self.uploaded = {}
        self.moved = []
        self.reconnected = 0
    def list_files(self, remote_dir): return self.files
    def download_file(self, remote_path, local_path):
        Path(local_path).write_text("<xml/>")
        return local_path
    def upload_bytes(self, payload, remote_path): self.uploaded[remote_path] = payload
    def move_file(self, source, destination): self.moved.append((source, destination))
    def delete_file(self, remote_path): self.deleted = remote_path
    def close(self): self.closed = True
    def reconnect(self): self.reconnected += 1


def test_sftp_service_delegates_file_operations(tmp_path):
    client = FakeClient()
    service = SftpService(client)  # type: ignore[arg-type]
    assert service.list_files("/inbound/stock/") == ["/inbound/stock/a.xml"]
    service.download_file("/inbound/stock/a.xml", tmp_path / "a.xml")
    service.upload_bytes(b"abc", "/outbound/orders/o.xml")
    service.move_file("a", "b")
    assert client.uploaded["/outbound/orders/o.xml"] == b"abc"
    assert client.moved == [("a", "b")]
