from __future__ import annotations

import asyncio

from core.repository import set_setting


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
