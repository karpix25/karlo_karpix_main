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


def test_encrypt_decrypt_with_runtime_key_file(monkeypatch, tmp_path) -> None:
    key_file = tmp_path / '.userbot-secrets.key'
    monkeypatch.delenv('USERBOT_SECRETS_KEY', raising=False)
    monkeypatch.setenv('USERBOT_SECRETS_KEY_FILE', key_file.as_posix())

    from core.config import get_settings

    get_settings.cache_clear()
    encrypted = encrypt_value('runtime-secret-value')
    assert encrypted.startswith('enc:v1:')
    assert key_file.exists()
    assert decrypt_value(encrypted) == 'runtime-secret-value'
