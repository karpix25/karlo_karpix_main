from __future__ import annotations

import asyncio
import os
from pathlib import Path
import re
import shutil
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

from core.repository import release_runtime_lock, try_acquire_runtime_lock

_SESSION_LOCKS: dict[str, asyncio.Lock] = {}
_LOCAL_LOCKS_GUARD = asyncio.Lock()
_LOCK_OWNER = f'telethon-worker:{uuid.uuid4().hex}'
_SESSION_NAME_RE = re.compile(r'[^A-Za-z0-9_.-]+')
_FALLBACK_SESSION_STORAGE_DIR = Path('./backend/telethon_sessions')


def normalize_session_name(raw_name: str | None, default: str = 'vaca_userbot') -> str:
    value = (raw_name or '').strip()
    if not value:
        return default
    value = value.replace('/', '_').replace('\\', '_')
    value = _SESSION_NAME_RE.sub('_', value).strip('._-')
    if not value:
        return default
    return value[:64]


def session_storage_path(session_name: str) -> str:
    """
    Returns stable session path that survives container redeploys.
    Also migrates legacy local session file on first access.
    """
    normalized = normalize_session_name(session_name)
    storage_dir = Path(os.getenv('TELETHON_SESSION_DIR', '/data/telethon_sessions'))
    try:
        storage_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        storage_dir = _FALLBACK_SESSION_STORAGE_DIR
        storage_dir.mkdir(parents=True, exist_ok=True)
    target = storage_dir / normalized

    # Telethon sqlite session file physically lives at "<name>.session".
    legacy = Path(f'./{normalized}.session')
    target_sqlite = Path(f'{target.as_posix()}.session')
    if legacy.exists() and not target_sqlite.exists():
        try:
            shutil.move(legacy.as_posix(), target_sqlite.as_posix())
        except OSError:
            # Best effort: continue with target path even if migration failed.
            pass

    return target.as_posix()


async def _get_local_lock(session_name: str) -> asyncio.Lock:
    async with _LOCAL_LOCKS_GUARD:
        lock = _SESSION_LOCKS.get(session_name)
        if lock is None:
            lock = asyncio.Lock()
            _SESSION_LOCKS[session_name] = lock
        return lock


@asynccontextmanager
async def telethon_operation_lock(session_name: str, ttl_seconds: int = 120) -> AsyncIterator[None]:
    local_lock = await _get_local_lock(session_name)
    async with local_lock:
        lock_key = f'telethon_session:{session_name}'
        while True:
            acquired = await try_acquire_runtime_lock(lock_key, _LOCK_OWNER, ttl_seconds)
            if acquired:
                break
            await asyncio.sleep(0.15)
        try:
            yield
        finally:
            await release_runtime_lock(lock_key, _LOCK_OWNER)
