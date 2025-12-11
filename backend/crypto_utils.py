import base64
import hashlib
import os
from typing import Optional

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def _derive_key(account: str) -> bytes:
    return hashlib.sha256(account.encode("utf-8")).digest()


def encrypt_password(account: str, password: str) -> str:
    key = _derive_key(account)
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(password.encode("utf-8")) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ct = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(iv + ct).decode("utf-8")


def decrypt_password(account: str, enc: str) -> Optional[str]:
    if not enc:
        return None
    key = _derive_key(account)
    raw = base64.b64decode(enc)
    iv, ct = raw[:16], raw[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded) + unpadder.finalize()
    return data.decode("utf-8")
