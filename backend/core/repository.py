from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .database import get_db
from .models import DraftPlatform, DraftStatus, RunStatus


@dataclass
class RawMessageInput:
    channel_username: str
    message_id: int
    text: str
    posted_at: str | None


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


async def create_pipeline_run(trigger_source: str) -> int:
    async with get_db() as db:
        cur = await db.execute(
            'INSERT INTO pipeline_runs(trigger_source, status) VALUES(?, ?)',
            (trigger_source, RunStatus.running.value),
        )
        await db.commit()
        return int(cur.lastrowid)


async def finish_pipeline_run(
    run_id: int,
    *,
    status: RunStatus,
    ingested_count: int,
    candidates_count: int,
    drafts_count: int,
    error: str | None = None,
) -> None:
    async with get_db() as db:
        await db.execute(
            '''
            UPDATE pipeline_runs
            SET status = ?, ingested_count = ?, candidates_count = ?, drafts_count = ?, error = ?, finished_at = ?
            WHERE id = ?
            ''',
            (status.value, ingested_count, candidates_count, drafts_count, error, utc_now_iso(), run_id),
        )
        await db.commit()


async def upsert_sources(channels: list[str]) -> None:
    normalized = sorted({c.strip() for c in channels if c.strip()})
    async with get_db() as db:
        await db.execute('UPDATE source_channels SET is_active = 0')
        for channel in normalized:
            await db.execute(
                '''
                INSERT INTO source_channels(channel_username, is_active)
                VALUES(?, 1)
                ON CONFLICT(channel_username)
                DO UPDATE SET is_active = 1
                ''',
                (channel,),
            )
        await db.commit()


async def list_active_sources() -> list[str]:
    async with get_db() as db:
        cur = await db.execute(
            'SELECT channel_username FROM source_channels WHERE is_active = 1 ORDER BY channel_username',
        )
        rows = await cur.fetchall()
        return [str(r['channel_username']) for r in rows]


async def insert_raw_message(message: RawMessageInput) -> int | None:
    async with get_db() as db:
        cur = await db.execute(
            '''
            INSERT OR IGNORE INTO raw_messages(channel_username, message_id, text, posted_at)
            VALUES(?, ?, ?, ?)
            ''',
            (
                message.channel_username,
                message.message_id,
                message.text,
                message.posted_at,
            ),
        )
        await db.commit()
        if cur.lastrowid == 0:
            return None
        return int(cur.lastrowid)


async def create_candidate(
    raw_message_id: int,
    summary: str,
    relevance_score: float,
    status: str,
    reason: str | None,
) -> int:
    async with get_db() as db:
        cur = await db.execute(
            '''
            INSERT INTO content_candidates(raw_message_id, summary, relevance_score, status, reason)
            VALUES(?, ?, ?, ?, ?)
            ''',
            (raw_message_id, summary, relevance_score, status, reason),
        )
        await db.commit()
        return int(cur.lastrowid)


async def create_draft(
    candidate_id: int,
    platform: DraftPlatform,
    content: str,
    cta: str | None,
    hashtags: str | None,
    status: DraftStatus,
) -> int:
    async with get_db() as db:
        cur = await db.execute(
            '''
            INSERT INTO drafts(candidate_id, platform, content, cta, hashtags, status)
            VALUES(?, ?, ?, ?, ?, ?)
            ''',
            (candidate_id, platform.value, content, cta, hashtags, status.value),
        )
        await db.commit()
        return int(cur.lastrowid)


async def list_inbox(status: str | None = None) -> list[dict[str, Any]]:
    query = '''
        SELECT
            c.id AS candidate_id,
            c.raw_message_id,
            r.channel_username,
            r.text,
            c.summary,
            c.relevance_score,
            c.status,
            c.reason,
            c.created_at
        FROM content_candidates c
        JOIN raw_messages r ON r.id = c.raw_message_id
    '''
    params: list[Any] = []
    if status:
        query += ' WHERE c.status = ?'
        params.append(status)
    query += ' ORDER BY c.created_at DESC'

    async with get_db() as db:
        cur = await db.execute(query, tuple(params))
        rows = await cur.fetchall()
        return [dict(row) for row in rows]


async def list_drafts(platform: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    query = 'SELECT * FROM drafts'
    params: list[str] = []

    clauses = []
    if platform:
        clauses.append('platform = ?')
        params.append(platform)
    if status:
        clauses.append('status = ?')
        params.append(status)

    if clauses:
        query += ' WHERE ' + ' AND '.join(clauses)

    query += ' ORDER BY created_at DESC'

    async with get_db() as db:
        cur = await db.execute(query, tuple(params))
        rows = await cur.fetchall()
        return [dict(row) for row in rows]


async def get_draft(draft_id: int) -> dict[str, Any] | None:
    async with get_db() as db:
        cur = await db.execute('SELECT * FROM drafts WHERE id = ?', (draft_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def update_draft(
    draft_id: int,
    *,
    content: str,
    cta: str | None,
    hashtags: str | None,
) -> None:
    async with get_db() as db:
        await db.execute(
            '''
            UPDATE drafts
            SET content = ?, cta = ?, hashtags = ?, updated_at = ?
            WHERE id = ?
            ''',
            (content, cta, hashtags, utc_now_iso(), draft_id),
        )
        await db.commit()


async def set_draft_status(
    draft_id: int,
    status: DraftStatus,
    publish_result: str | None = None,
    error: str | None = None,
) -> None:
    async with get_db() as db:
        await db.execute(
            '''
            UPDATE drafts
            SET status = ?, publish_result = ?, error = ?, updated_at = ?
            WHERE id = ?
            ''',
            (status.value, publish_result, error, utc_now_iso(), draft_id),
        )
        await db.commit()


async def get_setting(key: str) -> dict[str, Any]:
    async with get_db() as db:
        cur = await db.execute('SELECT value_json FROM settings WHERE key = ?', (key,))
        row = await cur.fetchone()
        if not row:
            return {}
        return json.loads(row['value_json'])


async def set_setting(key: str, value: dict[str, Any]) -> None:
    payload = json.dumps(value)
    async with get_db() as db:
        await db.execute(
            '''
            INSERT INTO settings(key, value_json, updated_at)
            VALUES(?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value_json = excluded.value_json,
                updated_at = excluded.updated_at
            ''',
            (key, payload, utc_now_iso()),
        )
        await db.commit()


async def draft_count_for_candidate(candidate_id: int) -> int:
    async with get_db() as db:
        cur = await db.execute('SELECT COUNT(1) AS cnt FROM drafts WHERE candidate_id = ?', (candidate_id,))
        row = await cur.fetchone()
        return int(row['cnt'])
