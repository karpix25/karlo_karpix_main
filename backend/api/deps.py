from __future__ import annotations

from fastapi import Depends

from core.auth import TelegramUser, get_current_user


def require_user(user: TelegramUser = Depends(get_current_user)) -> TelegramUser:
    return user
