from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from core.config import get_settings
from core.repository import (
    add_channel_guard_event,
    get_channel_guard_state,
    get_setting,
    set_channel_guard_state,
)
from core.repository import utc_now_iso
from core.secrets import decrypt_value
from services.telethon_runtime import normalize_session_name, session_storage_path, telethon_operation_lock

logger = logging.getLogger(__name__)


@dataclass
class IngestedMessage:
    channel_username: str
    message_id: int
    text: str
    posted_at: str


@dataclass
class FetchGuardMetrics:
    skipped_by_cooldown: int = 0
    floodwait_channels: int = 0
    retried_channels: int = 0
    guarded_errors: int = 0


@dataclass
class FetchMessagesResult:
    messages: list[IngestedMessage] = field(default_factory=list)
    metrics: FetchGuardMetrics = field(default_factory=FetchGuardMetrics)


class TelethonUserbotService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def _runtime_config(self) -> dict:
        payload = await get_setting('userbot')
        api_id = int(payload.get('api_id') or self.settings.telethon_api_id or 0)
        raw_hash = str(payload.get('api_hash') or '').strip()
        if raw_hash:
            try:
                api_hash = decrypt_value(raw_hash).strip()
            except ValueError:
                logger.warning('telethon api_hash decrypt failed; treating config as incomplete')
                api_hash = ''
        else:
            api_hash = str(self.settings.telethon_api_hash or '').strip()
        session_name = normalize_session_name(
            str(payload.get('session_name') or self.settings.telethon_session or 'vaca_userbot').strip(),
            default='vaca_userbot',
        )
        configured = bool(api_id and api_hash)
        return {
            'api_id': api_id,
            'api_hash': api_hash,
            'session_name': session_name or 'vaca_userbot',
            'configured': configured,
        }

    async def _anti_abuse_settings(self) -> dict[str, Any]:
        defaults = {
            'enabled': True,
            'messages_per_channel': 3,
            'channel_jitter_min_ms': 1500,
            'channel_jitter_max_ms': 4000,
            'batch_size': 10,
            'batch_pause_min_s': 15,
            'batch_pause_max_s': 45,
            'max_retries': 3,
            'retry_backoff_s': [2, 8, 20],
            'floodwait_extra_jitter_min_s': 1,
            'floodwait_extra_jitter_max_s': 5,
            'channel_error_threshold': 3,
            'channel_cooldown_default_s': 1800,
            'manual_bypass_cooldown': False,
        }
        payload = await get_setting('anti_abuse')
        merged = {**defaults, **(payload or {})}

        # Normalize bounds defensively.
        if int(merged['channel_jitter_min_ms']) > int(merged['channel_jitter_max_ms']):
            merged['channel_jitter_min_ms'], merged['channel_jitter_max_ms'] = (
                int(merged['channel_jitter_max_ms']),
                int(merged['channel_jitter_min_ms']),
            )
        if int(merged['batch_pause_min_s']) > int(merged['batch_pause_max_s']):
            merged['batch_pause_min_s'], merged['batch_pause_max_s'] = (
                int(merged['batch_pause_max_s']),
                int(merged['batch_pause_min_s']),
            )
        if int(merged['floodwait_extra_jitter_min_s']) > int(merged['floodwait_extra_jitter_max_s']):
            merged['floodwait_extra_jitter_min_s'], merged['floodwait_extra_jitter_max_s'] = (
                int(merged['floodwait_extra_jitter_max_s']),
                int(merged['floodwait_extra_jitter_min_s']),
            )

        return merged

    @staticmethod
    def _parse_iso(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _seconds_left(cooldown_until: datetime | None) -> int:
        if not cooldown_until:
            return 0
        now = datetime.now(tz=timezone.utc)
        return max(int((cooldown_until - now).total_seconds()), 0)

    async def _is_channel_in_cooldown(self, channel: str) -> tuple[bool, dict[str, Any] | None]:
        state = await get_channel_guard_state(channel)
        cooldown_until = self._parse_iso(state.get('cooldown_until') if state else None)
        return self._seconds_left(cooldown_until) > 0, state

    async def _mark_channel_success(self, channel: str) -> None:
        now = utc_now_iso()
        await set_channel_guard_state(
            channel,
            cooldown_until=None,
            last_ok_at=now,
            last_error_at=None,
            consecutive_errors=0,
            last_error_code=None,
        )
        await add_channel_guard_event(channel, 'channel_ok', {'at': now})

    async def _mark_channel_error(
        self,
        channel: str,
        *,
        state: dict[str, Any] | None,
        error_code: str,
        cooldown_seconds: int,
    ) -> None:
        now_dt = datetime.now(tz=timezone.utc)
        now_iso = now_dt.isoformat()
        cooldown_until = (now_dt + timedelta(seconds=max(cooldown_seconds, 0))).isoformat() if cooldown_seconds > 0 else None
        previous_errors = int((state or {}).get('consecutive_errors') or 0)

        await set_channel_guard_state(
            channel,
            cooldown_until=cooldown_until,
            last_ok_at=(state or {}).get('last_ok_at'),
            last_error_at=now_iso,
            consecutive_errors=previous_errors + 1,
            last_error_code=error_code,
        )
        await add_channel_guard_event(
            channel,
            'channel_error',
            {
                'error_code': error_code,
                'consecutive_errors': previous_errors + 1,
                'cooldown_seconds': cooldown_seconds,
                'cooldown_until': cooldown_until,
                'at': now_iso,
            },
        )

    async def _sleep_ms(self, min_ms: int, max_ms: int) -> None:
        if max_ms <= 0:
            return
        duration_ms = random.randint(max(0, min_ms), max_ms)
        if duration_ms > 0:
            await asyncio.sleep(duration_ms / 1000)

    async def _sleep_s(self, min_s: int, max_s: int) -> None:
        if max_s <= 0:
            return
        duration_s = random.randint(max(0, min_s), max_s)
        if duration_s > 0:
            await asyncio.sleep(duration_s)

    async def fetch_new_messages(
        self,
        channels: list[str],
        trigger_source: str = 'manual',
    ) -> FetchMessagesResult:
        result = FetchMessagesResult()
        if not channels:
            return result

        runtime = await self._runtime_config()
        anti_abuse = await self._anti_abuse_settings()
        guard_enabled = bool(anti_abuse.get('enabled', True))
        limit_per_channel = int(anti_abuse.get('messages_per_channel', 3))
        max_retries = int(anti_abuse.get('max_retries', 3))
        retry_backoff_s = [int(item) for item in anti_abuse.get('retry_backoff_s', [2, 8, 20]) if int(item) >= 0]
        threshold = int(anti_abuse.get('channel_error_threshold', 3))
        default_cooldown_s = int(anti_abuse.get('channel_cooldown_default_s', 1800))

        bypass_cooldown = bool(anti_abuse.get('manual_bypass_cooldown', False)) and trigger_source == 'manual'

        active_channels: list[str] = []
        for channel in channels:
            if not guard_enabled or bypass_cooldown:
                active_channels.append(channel)
                continue

            in_cooldown, state = await self._is_channel_in_cooldown(channel)
            if in_cooldown:
                result.metrics.skipped_by_cooldown += 1
                cooldown_until = (state or {}).get('cooldown_until')
                await add_channel_guard_event(
                    channel,
                    'skip_cooldown',
                    {'cooldown_until': cooldown_until, 'trigger_source': trigger_source},
                )
                continue

            active_channels.append(channel)

        # Fallback mode for local/dev and CI tests without Telegram credentials.
        if not runtime['configured']:
            now = datetime.now(tz=timezone.utc).isoformat()
            for idx, channel in enumerate(active_channels):
                result.messages.append(
                    IngestedMessage(
                        channel_username=channel,
                        message_id=int(datetime.now().timestamp()) + idx,
                        text=f'Практический пост из {channel} про AI, backend и продуктовые решения.',
                        posted_at=now,
                    )
                )
            return result

        from telethon import TelegramClient  # lazy import
        from telethon.errors import FloodWaitError

        retried_channels: set[str] = set()
        floodwait_channels: set[str] = set()

        client = TelegramClient(
            session_storage_path(runtime['session_name']),
            runtime['api_id'],
            runtime['api_hash'],
        )

        async with telethon_operation_lock(runtime['session_name']):
            async with client:
                for idx, channel in enumerate(active_channels):
                    state = await get_channel_guard_state(channel)
                    attempts = 0
                    channel_messages: list[IngestedMessage] = []
                    channel_success = False

                    while attempts <= max_retries:
                        try:
                            async for message in client.iter_messages(channel, limit=limit_per_channel):
                                if not message or not getattr(message, 'message', None):
                                    continue
                                channel_messages.append(
                                    IngestedMessage(
                                        channel_username=channel,
                                        message_id=int(message.id),
                                        text=str(message.message),
                                        posted_at=(message.date or datetime.now(tz=timezone.utc)).isoformat(),
                                    )
                                )
                            channel_success = True
                            break
                        except FloodWaitError as exc:
                            floodwait_channels.add(channel)
                            extra = random.randint(
                                int(anti_abuse.get('floodwait_extra_jitter_min_s', 1)),
                                int(anti_abuse.get('floodwait_extra_jitter_max_s', 5)),
                            )
                            cooldown_seconds = int(getattr(exc, 'seconds', 0)) + extra
                            await self._mark_channel_error(
                                channel,
                                state=state,
                                error_code='flood_wait',
                                cooldown_seconds=cooldown_seconds,
                            )
                            result.metrics.guarded_errors += 1
                            break
                        except Exception as exc:
                            attempts += 1
                            error_code = exc.__class__.__name__
                            if attempts <= max_retries:
                                retried_channels.add(channel)
                                backoff = retry_backoff_s[min(attempts - 1, len(retry_backoff_s) - 1)] if retry_backoff_s else 0
                                jitter = random.randint(0, 2)
                                await asyncio.sleep(max(backoff + jitter, 0))
                                continue

                            previous = int((state or {}).get('consecutive_errors') or 0)
                            cooldown_seconds = default_cooldown_s if previous + 1 >= threshold else 0
                            await self._mark_channel_error(
                                channel,
                                state=state,
                                error_code=error_code,
                                cooldown_seconds=cooldown_seconds,
                            )
                            result.metrics.guarded_errors += 1
                            break

                    if channel_success:
                        result.messages.extend(channel_messages)
                        await self._mark_channel_success(channel)

                    if guard_enabled and idx < len(active_channels) - 1:
                        await self._sleep_ms(
                            int(anti_abuse.get('channel_jitter_min_ms', 1500)),
                            int(anti_abuse.get('channel_jitter_max_ms', 4000)),
                        )

                    if (
                        guard_enabled
                        and int(anti_abuse.get('batch_size', 10)) > 0
                        and (idx + 1) % int(anti_abuse.get('batch_size', 10)) == 0
                        and idx < len(active_channels) - 1
                    ):
                        await self._sleep_s(
                            int(anti_abuse.get('batch_pause_min_s', 15)),
                            int(anti_abuse.get('batch_pause_max_s', 45)),
                        )

        result.metrics.retried_channels = len(retried_channels)
        result.metrics.floodwait_channels = len(floodwait_channels)
        return result

    async def publish_to_telegram(self, target_channel: str, text: str) -> str:
        runtime = await self._runtime_config()
        if not runtime['configured']:
            return f'mock://telegram/{target_channel}/{abs(hash(text)) % 10_000_000}'

        from telethon import TelegramClient  # lazy import

        client = TelegramClient(
            session_storage_path(runtime['session_name']),
            runtime['api_id'],
            runtime['api_hash'],
        )
        async with telethon_operation_lock(runtime['session_name']):
            async with client:
                msg = await client.send_message(target_channel, text)
                return f'https://t.me/{target_channel}/{msg.id}'
