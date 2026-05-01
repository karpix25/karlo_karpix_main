from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from core.config import get_settings
from core.repository import get_setting
from core.secrets import decrypt_value


@dataclass
class IngestedMessage:
    channel_username: str
    message_id: int
    text: str
    posted_at: str


class TelethonUserbotService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def _runtime_config(self) -> dict:
        payload = await get_setting('userbot')
        api_id = int(payload.get('api_id') or self.settings.telethon_api_id or 0)
        raw_hash = str(payload.get('api_hash') or '').strip()
        if raw_hash:
            api_hash = decrypt_value(raw_hash).strip()
        else:
            api_hash = str(self.settings.telethon_api_hash or '').strip()
        session_name = str(payload.get('session_name') or self.settings.telethon_session or 'vaca_userbot').strip()
        enabled = bool(payload.get('enabled', self.settings.telethon_enabled))
        configured = bool(api_id and api_hash)
        return {
            'api_id': api_id,
            'api_hash': api_hash,
            'session_name': session_name or 'vaca_userbot',
            'enabled': enabled and configured,
        }

    async def fetch_new_messages(self, channels: list[str], limit_per_channel: int = 5) -> list[IngestedMessage]:
        if not channels:
            return []

        runtime = await self._runtime_config()
        # Fallback mode for local/dev and CI tests without Telegram credentials.
        if not runtime['enabled']:
            now = datetime.now(tz=timezone.utc).isoformat()
            out: list[IngestedMessage] = []
            for idx, channel in enumerate(channels):
                out.append(
                    IngestedMessage(
                        channel_username=channel,
                        message_id=int(datetime.now().timestamp()) + idx,
                        text=f'Практический пост из {channel} про AI, backend и продуктовые решения.',
                        posted_at=now,
                    )
                )
            return out

        from telethon import TelegramClient  # lazy import

        client = TelegramClient(
            runtime['session_name'],
            runtime['api_id'],
            runtime['api_hash'],
        )
        out: list[IngestedMessage] = []
        async with client:
            for channel in channels:
                async for message in client.iter_messages(channel, limit=limit_per_channel):
                    if not message or not getattr(message, 'message', None):
                        continue
                    out.append(
                        IngestedMessage(
                            channel_username=channel,
                            message_id=int(message.id),
                            text=str(message.message),
                            posted_at=(message.date or datetime.now(tz=timezone.utc)).isoformat(),
                        )
                    )
        return out

    async def publish_to_telegram(self, target_channel: str, text: str) -> str:
        runtime = await self._runtime_config()
        if not runtime['enabled']:
            return f'mock://telegram/{target_channel}/{abs(hash(text)) % 10_000_000}'

        from telethon import TelegramClient  # lazy import

        client = TelegramClient(
            runtime['session_name'],
            runtime['api_id'],
            runtime['api_hash'],
        )
        async with client:
            msg = await client.send_message(target_channel, text)
            return f'https://t.me/{target_channel}/{msg.id}'
