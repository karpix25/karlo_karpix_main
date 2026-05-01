from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from .config import get_settings

_ENC_PREFIX = 'enc:v1:'


def _fernet_from_env() -> Fernet:
    settings = get_settings()
    raw = (settings.userbot_secrets_key or '').strip()
    if not raw:
        raise ValueError('userbot_secrets_key_not_configured')

    # Accept either a pre-generated Fernet key or an arbitrary passphrase.
    if len(raw) == 44:
        try:
            base64.urlsafe_b64decode(raw.encode())
            key = raw.encode()
            return Fernet(key)
        except Exception:
            pass

    derived = hashlib.sha256(raw.encode('utf-8')).digest()
    key = base64.urlsafe_b64encode(derived)
    return Fernet(key)


def encrypt_value(plain: str) -> str:
    if not plain:
        return ''
    fernet = _fernet_from_env()
    token = fernet.encrypt(plain.encode('utf-8')).decode('utf-8')
    return f'{_ENC_PREFIX}{token}'


def decrypt_value(value: str) -> str:
    if not value:
        return ''
    if not value.startswith(_ENC_PREFIX):
        # Backward compatibility for legacy plain-text rows.
        return value

    token = value[len(_ENC_PREFIX):]
    fernet = _fernet_from_env()
    try:
        return fernet.decrypt(token.encode('utf-8')).decode('utf-8')
    except InvalidToken as exc:
        raise ValueError('userbot_secret_decrypt_failed') from exc
