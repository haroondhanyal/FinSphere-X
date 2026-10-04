"""TOTP primitives for authenticator-app MFA."""

import base64
import binascii
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet() -> Fernet:
    wrapping_secret = settings.mfa_encryption_key or settings.jwt_secret
    key = base64.urlsafe_b64encode(
        hashlib.sha256(b"finspherex-totp:" + wrapping_secret.encode()).digest()
    )
    return Fernet(key)


def new_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def encrypt_totp_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode("ascii")).decode("ascii")


def decrypt_totp_secret(encrypted: str) -> str:
    try:
        return _fernet().decrypt(encrypted.encode("ascii")).decode("ascii")
    except (InvalidToken, ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Stored MFA secret cannot be decrypted") from exc


def provisioning_uri(secret: str, account_name: str) -> str:
    label = quote(f"FinSphere X:{account_name}", safe="")
    return f"otpauth://totp/{label}?secret={secret}&issuer=FinSphere%20X&algorithm=SHA1&digits=6&period=30"


def matching_counter(secret: str, code: str, now: int | None = None) -> int | None:
    if len(code) != 6 or not code.isascii() or not code.isdigit():
        return None
    padding = "=" * ((8 - len(secret) % 8) % 8)
    try:
        key = base64.b32decode(secret + padding, casefold=True)
    except (ValueError, binascii.Error):
        return None
    current = int((now if now is not None else time.time()) // 30)
    matches = []
    for counter in range(max(0, current - 1), current + 2):
        digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
        offset = digest[-1] & 0x0F
        binary = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
        candidate = f"{binary % 1_000_000:06d}"
        if hmac.compare_digest(candidate, code):
            matches.append(counter)
    return max(matches) if matches else None
