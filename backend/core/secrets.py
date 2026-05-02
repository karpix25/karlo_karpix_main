from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from .config import get_settings

_ENC_PREFIX = 'enc:v1:'
_DEFAULT_KEY_FILE = '/data/.userbot_secrets.key'
_FALLBACK_KEY_FILE = './backend/.userbot_secrets.key'


def _runtime_key_path() -> Path:
    raw_path = (os.getenv('USERBOT_SECRETS_KEY_FILE') or _DEFAULT_KEY_FILE).strip() or _DEFAULT_KEY_FILE
    return Path(raw_path)


def _load_or_create_runtime_key() -> str:
    def _read_or_create(path: Path) -> str:
        if path.exists():
            existing = path.read_text(encoding='utf-8').strip()
            if existing:
                return existing

        path.parent.mkdir(parents=True, exist_ok=True)
        generated = Fernet.generate_key().decode('utf-8')
        path.write_text(generated, encoding='utf-8')
        try:
            path.chmod(0o600)
        except OSError:
            # Best-effort hardening for environments without chmod support.
            pass
        return generated

    primary = _runtime_key_path()
    try:
        return _read_or_create(primary)
    except OSError:
        # Fallback for local/dev or restricted filesystems.
        return _read_or_create(Path(_FALLBACK_KEY_FILE))


def _fernet_from_env() -> Fernet:
    settings = get_settings()
    raw = (settings.userbot_secrets_key or '').strip()
    if not raw:
        raw = _load_or_create_runtime_key()

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
