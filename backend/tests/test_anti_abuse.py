from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import ModuleType

import pytest

from core.database import init_db
from core.repository import (
    add_channel_guard_event,
    get_channel_guard_state,
    list_channel_guard_events,
    set_channel_guard_state,
    set_setting,
)
from services.telethon_service import TelethonUserbotService


@pytest.mark.asyncio
async def test_fetch_skips_channel_on_cooldown() -> None:
    await init_db()
    await set_setting('userbot', {'api_id': 1, 'api_hash': 'x', 'session_name': 'vaca_userbot', 'enabled': False})
    await set_setting(
        'anti_abuse',
        {
            'enabled': True,
            'messages_per_channel': 3,
            'channel_jitter_min_ms': 0,
            'channel_jitter_max_ms': 0,
            'batch_size': 10,
            'batch_pause_min_s': 0,
            'batch_pause_max_s': 0,
            'max_retries': 0,
            'retry_backoff_s': [0],
            'floodwait_extra_jitter_min_s': 0,
            'floodwait_extra_jitter_max_s': 0,
            'channel_error_threshold': 3,
            'channel_cooldown_default_s': 600,
            'manual_bypass_cooldown': False,
        },
    )
    await set_channel_guard_state(
        '@cooldown_channel',
        cooldown_until=(datetime.now(tz=timezone.utc) + timedelta(minutes=5)).isoformat(),
        last_ok_at=None,
        last_error_at=datetime.now(tz=timezone.utc).isoformat(),
        consecutive_errors=2,
        last_error_code='flood_wait',
    )

    service = TelethonUserbotService()
    result = await service.fetch_new_messages(['@cooldown_channel'], trigger_source='manual')

    assert len(result.messages) == 0
    assert result.metrics.skipped_by_cooldown == 1


@pytest.mark.asyncio
async def test_manual_bypass_cooldown_when_enabled() -> None:
    await init_db()
    await set_setting('userbot', {'api_id': 1, 'api_hash': 'x', 'session_name': 'vaca_userbot', 'enabled': False})
    await set_setting(
        'anti_abuse',
        {
            'enabled': True,
            'messages_per_channel': 3,
            'channel_jitter_min_ms': 0,
            'channel_jitter_max_ms': 0,
            'batch_size': 10,
            'batch_pause_min_s': 0,
            'batch_pause_max_s': 0,
            'max_retries': 0,
            'retry_backoff_s': [0],
            'floodwait_extra_jitter_min_s': 0,
            'floodwait_extra_jitter_max_s': 0,
            'channel_error_threshold': 3,
            'channel_cooldown_default_s': 600,
            'manual_bypass_cooldown': True,
        },
    )
    await set_channel_guard_state(
        '@cooldown_channel',
        cooldown_until=(datetime.now(tz=timezone.utc) + timedelta(minutes=5)).isoformat(),
        last_ok_at=None,
        last_error_at=datetime.now(tz=timezone.utc).isoformat(),
        consecutive_errors=2,
        last_error_code='flood_wait',
    )

    service = TelethonUserbotService()
    result = await service.fetch_new_messages(['@cooldown_channel'], trigger_source='manual')

    assert len(result.messages) == 1
    assert result.metrics.skipped_by_cooldown == 0


@pytest.mark.asyncio
async def test_floodwait_sets_cooldown_and_continues(monkeypatch: pytest.MonkeyPatch) -> None:
    await init_db()
    await set_setting('userbot', {'api_id': 123, 'api_hash': 'plain_hash', 'session_name': 'vaca_userbot', 'enabled': True})
    await set_setting(
        'anti_abuse',
        {
            'enabled': True,
            'messages_per_channel': 1,
            'channel_jitter_min_ms': 0,
            'channel_jitter_max_ms': 0,
            'batch_size': 10,
            'batch_pause_min_s': 0,
            'batch_pause_max_s': 0,
            'max_retries': 0,
            'retry_backoff_s': [0],
            'floodwait_extra_jitter_min_s': 0,
            'floodwait_extra_jitter_max_s': 0,
            'channel_error_threshold': 3,
            'channel_cooldown_default_s': 600,
            'manual_bypass_cooldown': False,
        },
    )

    bad_channel = '@bad_floodwait_case'
    good_channel = '@good_floodwait_case'

    class FakeFloodWaitError(Exception):
        def __init__(self, seconds: int):
            super().__init__('flood wait')
            self.seconds = seconds

    @dataclass
    class FakeMessage:
        id: int
        message: str
        date: datetime

    class FakeTelegramClient:
        def __init__(self, session: str, api_id: int, api_hash: str) -> None:
            _ = session, api_id, api_hash

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def iter_messages(self, channel: str, limit: int = 1):
            _ = limit
            if channel == bad_channel:
                raise FakeFloodWaitError(10)
            yield FakeMessage(id=1, message='ok msg', date=datetime.now(tz=timezone.utc))

    telethon_module = ModuleType('telethon')
    telethon_module.TelegramClient = FakeTelegramClient
    telethon_errors_module = ModuleType('telethon.errors')
    telethon_errors_module.FloodWaitError = FakeFloodWaitError

    monkeypatch.setitem(sys.modules, 'telethon', telethon_module)
    monkeypatch.setitem(sys.modules, 'telethon.errors', telethon_errors_module)

    service = TelethonUserbotService()
    result = await service.fetch_new_messages([bad_channel, good_channel], trigger_source='scheduler')

    assert len(result.messages) == 1
    assert result.messages[0].channel_username == good_channel
    assert result.metrics.floodwait_channels == 1
    assert result.metrics.guarded_errors == 1

    bad_state = await get_channel_guard_state(bad_channel)
    assert bad_state is not None
    assert bad_state['cooldown_until']
    assert int(bad_state['consecutive_errors']) == 1
    assert bad_state['last_error_code'] == 'flood_wait'


@pytest.mark.asyncio
async def test_guard_events_payload_is_json() -> None:
    await init_db()
    await add_channel_guard_event('@demo', 'sample', {'x': 1})
    events = await list_channel_guard_events(limit=1)
    assert events[0]['event_payload']['x'] == 1
