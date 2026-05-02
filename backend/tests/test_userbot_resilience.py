from __future__ import annotations

import asyncio
from pathlib import Path
import sys
from types import ModuleType

from core.repository import set_setting
from services.telethon_runtime import session_storage_path


def auth_headers() -> dict[str, str]:
    return {'X-Telegram-Init-Data': 'user_id=1&username=tester'}


def test_userbot_endpoints_handle_invalid_encrypted_hash(client) -> None:
    asyncio.run(
        set_setting(
            'userbot',
            {
                'api_id': 12345,
                'api_hash': 'enc:v1:this-is-not-a-valid-fernet-token',
                'session_name': 'vaca_userbot',
            },
        )
    )

    config_resp = client.get('/api/settings/userbot/config', headers=auth_headers())
    assert config_resp.status_code == 200
    assert config_resp.json()['has_api_hash'] is False

    status_resp = client.get('/api/settings/userbot/status', headers=auth_headers())
    assert status_resp.status_code == 200
    assert status_resp.json()['configured'] is False


def test_userbot_status_handles_telethon_session_lock_errors(client, monkeypatch) -> None:
    asyncio.run(
        set_setting(
            'userbot',
            {
                'api_id': 12345,
                'api_hash': 'plain_hash_value',
                'session_name': 'vaca_userbot',
            },
        )
    )

    class BrokenTelegramClient:
        def __init__(self, session: str, api_id: int, api_hash: str) -> None:
            _ = session, api_id, api_hash

        async def connect(self) -> None:
            raise RuntimeError('database is locked')

        async def disconnect(self) -> None:
            raise RuntimeError('database is locked')

    telethon_module = ModuleType('telethon')
    telethon_module.TelegramClient = BrokenTelegramClient
    monkeypatch.setitem(sys.modules, 'telethon', telethon_module)

    status_resp = client.get('/api/settings/userbot/status', headers=auth_headers())
    assert status_resp.status_code == 200
    payload = status_resp.json()
    assert payload['configured'] is True
    assert payload['authorized'] is False


def test_userbot_config_sanitizes_session_name(client) -> None:
    headers = auth_headers()
    put_resp = client.put(
        '/api/settings/userbot/config',
        json={
            'api_id': 123,
            'api_hash': 'abc123',
            'session_name': '../../very/unsafe\\\\name?.session',
        },
        headers=headers,
    )
    assert put_resp.status_code == 200
    payload = put_resp.json()
    assert payload['session_name'] == 'very_unsafe__name_.session'


def test_session_file_migrates_to_persistent_storage(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    storage_dir = tmp_path / 'persistent' / 'telethon_sessions'
    monkeypatch.setenv('TELETHON_SESSION_DIR', storage_dir.as_posix())

    legacy = tmp_path / 'vaca_userbot.session'
    legacy.write_text('legacy-session-content', encoding='utf-8')

    session_base = session_storage_path('vaca_userbot')
    assert session_base == (storage_dir / 'vaca_userbot').as_posix()
    assert legacy.exists() is False
    migrated = storage_dir / 'vaca_userbot.session'
    assert migrated.exists() is True
