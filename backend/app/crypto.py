import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.config import get_settings

_settings = get_settings()


def _derive_fernet_key() -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"sastia-api-key-encryption-salt-v1",
        iterations=600_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(_settings.SECRET_KEY.encode()))
    return key


_fernet = Fernet(_derive_fernet_key())


def encrypt_api_key(plaintext: str | None) -> str | None:
    if plaintext is None:
        return None
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_api_key(ciphertext: str | None) -> str | None:
    if ciphertext is None:
        return None
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except Exception:
        return ciphertext


def mask_api_key(api_key: str | None) -> str | None:
    if api_key is None:
        return None
    if len(api_key) <= 8:
        return api_key[:2] + "****"
    return api_key[:4] + "****" + api_key[-4:]
