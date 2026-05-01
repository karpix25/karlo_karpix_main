from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Annotated
from urllib.parse import parse_qsl

from fastapi import Depends, Header, HTTPException, status

from .config import Settings, get_settings


@dataclass
class TelegramUser:
    user_id: int
    username: str | None
    raw: dict


def _build_data_check_string(init_data: str) -> tuple[str, str]:
    pairs = parse_qsl(init_data, keep_blank_values=True)
    payload = dict(pairs)
    received_hash = payload.pop('hash', '')
    if not received_hash:
        raise ValueError('Missing hash in initData')

    lines = [f'{k}={v}' for k, v in sorted(payload.items(), key=lambda item: item[0])]
    return '\n'.join(lines), received_hash


def validate_init_data(init_data: str, bot_token: str, max_age_seconds: int) -> TelegramUser:
    data_check_string, received_hash = _build_data_check_string(init_data)

    secret_key = hmac.new(b'WebAppData', bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(received_hash, expected_hash):
        raise ValueError('Invalid initData signature')

    payload = dict(parse_qsl(init_data, keep_blank_values=True))
    auth_date = int(payload.get('auth_date', '0'))
    now = int(time.time())
    if auth_date <= 0 or now - auth_date > max_age_seconds:
        raise ValueError('Expired initData')

    user_blob = payload.get('user')
    if not user_blob:
        raise ValueError('initData has no user payload')

    user_payload = json.loads(user_blob)
    return TelegramUser(
        user_id=int(user_payload.get('id', 0)),
        username=user_payload.get('username'),
        raw=user_payload,
    )


def _extract_fake_user(init_data: str) -> TelegramUser:
    payload = dict(parse_qsl(init_data, keep_blank_values=True))
    user_id = int(payload.get('user_id', '1'))
    username = payload.get('username', 'dev_user')
    return TelegramUser(user_id=user_id, username=username, raw=payload)


async def get_current_user(
    init_data: Annotated[str | None, Header(alias='X-Telegram-Init-Data')] = None,
    settings: Settings = Depends(get_settings),
) -> TelegramUser:
    if not init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing X-Telegram-Init-Data header',
        )

    if settings.auth_allow_insecure_dev and not settings.telegram_bot_token:
        user = _extract_fake_user(init_data)
    else:
        if not settings.telegram_bot_token:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='telegram_bot_token_not_configured',
            )

        try:
            user = validate_init_data(
                init_data=init_data,
                bot_token=settings.telegram_bot_token,
                max_age_seconds=settings.telegram_initdata_max_age_seconds,
            )
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    if settings.admin_user_id > 0 and user.user_id != settings.admin_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='forbidden_for_user',
        )

    return user
