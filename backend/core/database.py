from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import aiosqlite

from .config import get_settings


SCHEMA_SQL = '''
CREATE TABLE IF NOT EXISTS source_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_username TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_username TEXT NOT NULL,
    message_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    posted_at TEXT,
    fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel_username, message_id)
);

CREATE TABLE IF NOT EXISTS content_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_message_id INTEGER NOT NULL UNIQUE,
    summary TEXT NOT NULL,
    relevance_score REAL NOT NULL,
    status TEXT NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(raw_message_id) REFERENCES raw_messages(id)
);

CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    content TEXT NOT NULL,
    cta TEXT,
    hashtags TEXT,
    status TEXT NOT NULL,
    publish_result TEXT,
    error TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(candidate_id) REFERENCES content_candidates(id)
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_source TEXT NOT NULL,
    status TEXT NOT NULL,
    ingested_count INTEGER NOT NULL DEFAULT 0,
    candidates_count INTEGER NOT NULL DEFAULT 0,
    drafts_count INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_candidates_status ON content_candidates(status);
CREATE INDEX IF NOT EXISTS idx_drafts_platform_status ON drafts(platform, status);
'''

DEFAULT_SETTINGS = {
    'sources': {'channels': []},
    'schedule': {'interval_minutes': 30},
    'skills': {
        'strict_links': True,
        'ban_giveaways': True,
        'prefer_technical_content': True,
    },
    'userbot': {
        'api_id': 0,
        'api_hash': '',
        'session_name': 'vaca_userbot',
        'enabled': False,
    },
}


@asynccontextmanager
async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    settings = get_settings()
    db_path = Path(settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(db_path.as_posix())
    conn.row_factory = aiosqlite.Row
    try:
        yield conn
    finally:
        await conn.close()


async def init_db() -> None:
    async with get_db() as db:
        await db.executescript(SCHEMA_SQL)
        for key, value in DEFAULT_SETTINGS.items():
            await db.execute(
                '''
                INSERT OR IGNORE INTO settings(key, value_json)
                VALUES (?, json(?))
                ''',
                (key, json.dumps(value)),
            )
        await db.commit()
