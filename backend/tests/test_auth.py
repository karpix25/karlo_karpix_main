from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from core.auth import validate_init_data


def _build_signed_init_data(bot_token: str, user_id: int = 42) -> str:
    payload = {
        'auth_date': str(int(time.time())),
        'query_id': 'AAEAAAE',
        'user': json.dumps({'id': user_id, 'username': 'carlo'}, separators=(',', ':')),
    }

    data_check = '\n'.join([f'{k}={payload[k]}' for k in sorted(payload.keys())])
    secret_key = hmac.new(b'WebAppData', bot_token.encode(), hashlib.sha256).digest()
    payload['hash'] = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()
    return urlencode(payload)


def test_validate_init_data_success() -> None:
    bot_token = '123:abc'
    init_data = _build_signed_init_data(bot_token)
    user = validate_init_data(init_data, bot_token=bot_token, max_age_seconds=3600)
    assert user.user_id == 42
    assert user.username == 'carlo'


def test_validate_init_data_fails_on_invalid_hash() -> None:
    bot_token = '123:abc'
    init_data = _build_signed_init_data(bot_token) + 'x'
    with pytest.raises(ValueError):
        validate_init_data(init_data, bot_token=bot_token, max_age_seconds=3600)


def test_admin_only_insecure_dev(client, monkeypatch) -> None:
    monkeypatch.setenv('ADMIN_USER_ID', '42')
    from core.config import get_settings

    get_settings.cache_clear()
    response = client.get('/api/inbox?status=accepted', headers={'X-Telegram-Init-Data': 'user_id=1&username=tester'})
    assert response.status_code == 403
