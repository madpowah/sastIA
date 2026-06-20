import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.config import get_settings

_settings = get_settings()

_LEGACY_SALT = b"sastia-api-key-encryption-salt-v1"


def _derive_fernet_key(salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(_settings.SECRET_KEY.encode()))
    return key


def encrypt_api_key(plaintext: str | None) -> str | None:
    if plaintext is None:
        return None
    salt = os.urandom(16)
    key = _derive_fernet_key(salt)
    f = Fernet(key)
    token = f.encrypt(plaintext.encode())
    return base64.b64encode(salt + token).decode()


def decrypt_api_key(ciphertext: str | None) -> str | None:
    if ciphertext is None:
        return None
    try:
        raw = base64.b64decode(ciphertext.encode())
        salt = raw[:16]
        token = raw[16:]
        key = _derive_fernet_key(salt)
        f = Fernet(key)
        return f.decrypt(token).decode()
    except Exception:
        pass
    try:
        key = _derive_fernet_key(_LEGACY_SALT)
        f = Fernet(key)
        return f.decrypt(ciphertext.encode()).decode()
    except Exception:
        return ciphertext


def mask_api_key(api_key: str | None) -> str | None:
    if api_key is None:
        return None
    if len(api_key) <= 8:
        return api_key[:2] + "****"
    return api_key[:4] + "****" + api_key[-4:]
