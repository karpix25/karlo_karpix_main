from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Any

from .database import get_db
from .models import DraftPlatform, DraftStatus, RunStatus


@dataclass
class RawMessageInput:
    channel_username: str
    message_id: int
    text: str
    media_type: str | None = None
    media_paths_json: str | None = None
    posted_at: str | None = None


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


async def has_running_pipeline_run() -> bool:
    async with get_db() as db:
        cur = await db.execute(
            '''
            SELECT 1
            FROM pipeline_runs
            WHERE status = ?
            LIMIT 1
            ''',
            (RunStatus.running.value,),
        )
        row = await cur.fetchone()
        return row is not None


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


async def try_acquire_runtime_lock(lock_key: str, owner: str, ttl_seconds: int) -> bool:
    now_epoch = int(time.time())
    expires_epoch = now_epoch + max(int(ttl_seconds), 1)
    async with get_db() as db:
        cur = await db.execute(
            '''
            INSERT INTO runtime_locks(lock_key, owner, acquired_at_epoch, expires_at_epoch)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(lock_key) DO UPDATE SET
                owner = excluded.owner,
                acquired_at_epoch = excluded.acquired_at_epoch,
                expires_at_epoch = excluded.expires_at_epoch
            WHERE runtime_locks.expires_at_epoch < excluded.acquired_at_epoch
               OR runtime_locks.owner = excluded.owner
            ''',
            (lock_key, owner, now_epoch, expires_epoch),
        )
        await db.commit()
        return cur.rowcount > 0


async def release_runtime_lock(lock_key: str, owner: str) -> None:
    async with get_db() as db:
        await db.execute(
            'DELETE FROM runtime_locks WHERE lock_key = ? AND owner = ?',
            (lock_key, owner),
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
            INSERT OR IGNORE INTO raw_messages(channel_username, message_id, text, media_type, media_paths_json, posted_at)
            VALUES(?, ?, ?, ?, ?, ?)
            ''',
            (
                message.channel_username,
                message.message_id,
                message.text,
                message.media_type,
                message.media_paths_json,
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
            r.media_type,
            r.media_paths_json,
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
        out = []
        for row in rows:
            d = dict(row)
            try:
                d['media_paths'] = json.loads(d.pop('media_paths_json') or '[]')
            except Exception:
                d['media_paths'] = []
            out.append(d)
        return out

async def record_user_decision(
    candidate_id: int,
    original_text: str,
    original_media_type: str | None,
    chosen_format: str,
    generated_content: str | None
) -> None:
    async with get_db() as db:
        await db.execute(
            '''
            INSERT INTO user_decisions(candidate_id, original_text, original_media_type, chosen_format, generated_content)
            VALUES(?, ?, ?, ?, ?)
            ''',
            (candidate_id, original_text, original_media_type, chosen_format, generated_content)
        )
        await db.commit()


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


async def get_channel_guard_state(channel_username: str) -> dict[str, Any] | None:
    async with get_db() as db:
        cur = await db.execute(
            'SELECT * FROM channel_guard_state WHERE channel_username = ?',
            (channel_username,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def set_channel_guard_state(
    channel_username: str,
    *,
    cooldown_until: str | None,
    last_ok_at: str | None,
    last_error_at: str | None,
    consecutive_errors: int,
    last_error_code: str | None,
) -> None:
    async with get_db() as db:
        await db.execute(
            '''
            INSERT INTO channel_guard_state(
                channel_username,
                cooldown_until,
                last_ok_at,
                last_error_at,
                consecutive_errors,
                last_error_code,
                updated_at
            )
            VALUES(?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(channel_username) DO UPDATE SET
                cooldown_until = excluded.cooldown_until,
                last_ok_at = excluded.last_ok_at,
                last_error_at = excluded.last_error_at,
                consecutive_errors = excluded.consecutive_errors,
                last_error_code = excluded.last_error_code,
                updated_at = excluded.updated_at
            ''',
            (
                channel_username,
                cooldown_until,
                last_ok_at,
                last_error_at,
                consecutive_errors,
                last_error_code,
                utc_now_iso(),
            ),
        )
        await db.commit()


async def add_channel_guard_event(channel_username: str, event_type: str, payload: dict[str, Any]) -> None:
    async with get_db() as db:
        await db.execute(
            '''
            INSERT INTO channel_guard_events(channel_username, event_type, event_payload_json)
            VALUES(?, ?, ?)
            ''',
            (channel_username, event_type, json.dumps(payload)),
        )
        await db.commit()


async def list_channel_cooldowns(limit: int = 200) -> list[dict[str, Any]]:
    async with get_db() as db:
        cur = await db.execute(
            '''
            SELECT
                channel_username,
                cooldown_until,
                consecutive_errors,
                last_error_code
            FROM channel_guard_state
            WHERE
                cooldown_until IS NOT NULL
                AND julianday(cooldown_until) > julianday('now')
            ORDER BY cooldown_until ASC
            LIMIT ?
            ''',
            (limit,),
        )
        rows = await cur.fetchall()
        return [dict(row) for row in rows]


async def list_channel_guard_events(limit: int = 100) -> list[dict[str, Any]]:
    async with get_db() as db:
        cur = await db.execute(
            '''
            SELECT id, channel_username, event_type, event_payload_json, created_at
            FROM channel_guard_events
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            ''',
            (limit,),
        )
        rows = await cur.fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            payload_raw = row['event_payload_json']
            try:
                payload = json.loads(payload_raw) if payload_raw else {}
            except Exception:
                payload = {}
            out.append(
                {
                    'id': int(row['id']),
                    'channel_username': str(row['channel_username']),
                    'event_type': str(row['event_type']),
                    'event_payload': payload,
                    'created_at': str(row['created_at']),
                }
            )
        return out
