from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from core.config import get_settings
from core.repository import get_setting
from core.secrets import decrypt_value


@dataclass
class PendingLogin:
    phone: str
    phone_code_hash: str
    created_at: datetime


class UserbotAuthService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._pending: dict[str, PendingLogin] = {}

    async def _runtime_config(self) -> dict:
        payload = await get_setting('userbot')
        api_id = int(payload.get('api_id') or self.settings.telethon_api_id or 0)
        raw_hash = str(payload.get('api_hash') or '').strip()
        if raw_hash:
            api_hash = decrypt_value(raw_hash).strip()
        else:
            api_hash = str(self.settings.telethon_api_hash or '').strip()
        session_name = str(payload.get('session_name') or self.settings.telethon_session or 'vaca_userbot').strip()
        return {
            'api_id': api_id,
            'api_hash': api_hash,
            'session_name': session_name or 'vaca_userbot',
        }

    def _is_configured(self, config: dict) -> bool:
        return bool(config.get('api_id') and config.get('api_hash'))

    def _make_client(self, config: dict):
        from telethon import TelegramClient

        return TelegramClient(
            config['session_name'],
            config['api_id'],
            config['api_hash'],
        )

    async def status(self) -> dict:
        config = await self._runtime_config()
        if not self._is_configured(config):
            return {
                'configured': False,
                'authorized': False,
                'session_name': config['session_name'],
                'me_username': None,
                'me_phone': None,
                'requires_2fa': False,
                'pending_phone': None,
                'pending_at': None,
            }

        client = self._make_client(config)
        authorized = False
        me_username = None
        me_phone = None
        try:
            await client.connect()
            authorized = await client.is_user_authorized()
            if authorized:
                me = await client.get_me()
                if me:
                    me_username = getattr(me, 'username', None)
                    me_phone = getattr(me, 'phone', None)
        finally:
            await client.disconnect()

        pending_phone = None
        pending_at = None
        if self._pending:
            latest = max(self._pending.values(), key=lambda item: item.created_at)
            pending_phone = latest.phone
            pending_at = latest.created_at.isoformat()

        return {
            'configured': True,
            'authorized': authorized,
            'session_name': config['session_name'],
            'me_username': me_username,
            'me_phone': me_phone,
            'requires_2fa': False,
            'pending_phone': pending_phone,
            'pending_at': pending_at,
        }

    async def send_code(self, phone: str) -> dict:
        config = await self._runtime_config()
        if not self._is_configured(config):
            raise ValueError('telethon_not_configured')

        normalized = phone.strip()
        if not normalized:
            raise ValueError('phone_required')

        client = self._make_client(config)
        try:
            await client.connect()
            sent = await client.send_code_request(normalized)
            self._pending[normalized] = PendingLogin(
                phone=normalized,
                phone_code_hash=sent.phone_code_hash,
                created_at=datetime.now(tz=timezone.utc),
            )
        finally:
            await client.disconnect()

        return {'status': 'code_sent', 'phone': normalized}

    async def sign_in(self, phone: str, code: str | None, password: str | None) -> dict:
        config = await self._runtime_config()
        if not self._is_configured(config):
            raise ValueError('telethon_not_configured')

        normalized = phone.strip()
        if not normalized:
            raise ValueError('phone_required')

        client = self._make_client(config)
        try:
            await client.connect()

            if password:
                await client.sign_in(password=password)
            else:
                pending = self._pending.get(normalized)
                if not pending:
                    raise ValueError('code_not_requested')
                if not code:
                    raise ValueError('code_required')
                try:
                    await client.sign_in(
                        phone=normalized,
                        code=code.strip(),
                        phone_code_hash=pending.phone_code_hash,
                    )
                except Exception as exc:
                    from telethon.errors import SessionPasswordNeededError

                    if isinstance(exc, SessionPasswordNeededError):
                        return {
                            'authorized': False,
                            'requires_2fa': True,
                            'status': 'password_required',
                        }
                    raise

            authorized = await client.is_user_authorized()
            me = await client.get_me() if authorized else None
            self._pending.pop(normalized, None)
            return {
                'authorized': authorized,
                'requires_2fa': False,
                'status': 'authorized' if authorized else 'not_authorized',
                'me_username': getattr(me, 'username', None) if me else None,
                'me_phone': getattr(me, 'phone', None) if me else None,
            }
        finally:
            await client.disconnect()

    async def logout(self) -> dict:
        config = await self._runtime_config()
        if not self._is_configured(config):
            raise ValueError('telethon_not_configured')

        client = self._make_client(config)
        try:
            await client.connect()
            await client.log_out()
        finally:
            await client.disconnect()

        self._pending.clear()
        return {'status': 'logged_out'}

    async def list_channels(self, limit: int = 200) -> list[dict]:
        config = await self._runtime_config()
        if not self._is_configured(config):
            raise ValueError('telethon_not_configured')

        client = self._make_client(config)
        channels: list[dict] = []
        try:
            await client.connect()
            authorized = await client.is_user_authorized()
            if not authorized:
                raise ValueError('userbot_not_authorized')

            async for dialog in client.iter_dialogs(limit=limit):
                entity = dialog.entity
                if not entity:
                    continue

                # Keep only dialogs that can be used by username in source settings.
                username = getattr(entity, 'username', None)
                if not username:
                    continue

                channels.append(
                    {
                        'title': dialog.name,
                        'username': f'@{username}',
                        'id': int(getattr(entity, 'id', 0) or 0),
                    }
                )
        finally:
            await client.disconnect()

        channels.sort(key=lambda item: item['title'].lower())
        return channels


userbot_auth_service = UserbotAuthService()
