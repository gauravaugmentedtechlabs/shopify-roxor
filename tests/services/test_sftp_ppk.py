from app.services.sftp.client import SftpClient


def test_detects_putty_ppk_key_text():
    key_text = "PuTTY-User-Key-File-3: ssh-rsa\nEncryption: none\n"
    assert SftpClient()._is_putty_ppk(key_text) is True


def test_non_ppk_key_text_is_not_detected_as_putty():
    key_text = "-----BEGIN OPENSSH PRIVATE KEY-----\n"
    assert SftpClient()._is_putty_ppk(key_text) is False
