from __future__ import annotations

from core.secrets import decrypt_value, encrypt_value


def test_encrypt_decrypt_roundtrip(monkeypatch) -> None:
    monkeypatch.setenv('USERBOT_SECRETS_KEY', 'roundtrip-secret-key')

    from core.config import get_settings

    get_settings.cache_clear()
    encrypted = encrypt_value('hash-secret-value')
    assert encrypted.startswith('enc:v1:')
    plain = decrypt_value(encrypted)
    assert plain == 'hash-secret-value'
