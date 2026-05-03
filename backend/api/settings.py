from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from api.deps import require_user
from core.repository import (
    get_setting,
    list_channel_cooldowns,
    list_channel_guard_events,
    set_setting,
    upsert_sources,
)
from core.secrets import decrypt_value, encrypt_value
from schemas import (
    AntiAbuseSettings,
    ChannelCooldownItem,
    ChannelGuardEventItem,
    ChannelGuardStatusResponse,
    MemoryPreview,
    ScheduleSettings,
    SkillsSettings,
    SourceSettings,
    UserbotActionResponse,
    UserbotChannelItem,
    UserbotConfigResponse,
    UserbotConfigUpdateRequest,
    UserbotSendCodeRequest,
    UserbotSignInRequest,
    UserbotStatusResponse,
)
from services.telethon_runtime import normalize_session_name
from services.userbot_auth_service import userbot_auth_service

router = APIRouter(prefix='/api/settings', tags=['settings'])


@router.get('/sources', response_model=SourceSettings)
async def get_sources(_user=Depends(require_user)) -> SourceSettings:
    payload = await get_setting('sources')
    return SourceSettings(**payload)


@router.put('/sources', response_model=SourceSettings)
async def update_sources(payload: SourceSettings, _user=Depends(require_user)) -> SourceSettings:
    # Auto-join channels if they look like invite links
    from services.telethon_service import TelethonUserbotService
    userbot = TelethonUserbotService()
    
    normalized_channels = []
    for channel in payload.channels:
        if 't.me/' in channel or channel.startswith('+'):
            try:
                # Try to join and get a cleaner username/id
                clean_name = await userbot.join_channel_by_link(channel)
                if not clean_name.startswith('@') and not clean_name.startswith('-'):
                    clean_name = f"@{clean_name}"
                normalized_channels.append(clean_name)
            except Exception:
                normalized_channels.append(channel)
        else:
            normalized_channels.append(channel)
            
    payload.channels = normalized_channels
    await set_setting('sources', payload.model_dump())
    await upsert_sources(payload.channels)
    return payload


@router.get('/anti-abuse', response_model=AntiAbuseSettings)
async def get_anti_abuse_settings(_user=Depends(require_user)) -> AntiAbuseSettings:
    payload = await get_setting('anti_abuse')
    return AntiAbuseSettings(**payload)


@router.put('/anti-abuse', response_model=AntiAbuseSettings)
async def update_anti_abuse_settings(
    payload: AntiAbuseSettings,
    _user=Depends(require_user),
) -> AntiAbuseSettings:
    await set_setting('anti_abuse', payload.model_dump())
    return payload


@router.get('/anti-abuse/guard-status', response_model=ChannelGuardStatusResponse)
async def get_channel_guard_status(_user=Depends(require_user)) -> ChannelGuardStatusResponse:
    cooldown_rows = await list_channel_cooldowns(limit=200)
    event_rows = await list_channel_guard_events(limit=100)

    cooldowns: list[ChannelCooldownItem] = []
    now = datetime.now(tz=timezone.utc)
    for row in cooldown_rows:
        raw = row.get('cooldown_until')
        if not raw:
            continue
        try:
            cooldown_until_dt = datetime.fromisoformat(raw)
        except ValueError:
            continue
        if cooldown_until_dt.tzinfo is None:
            cooldown_until_dt = cooldown_until_dt.replace(tzinfo=timezone.utc)
        seconds_left = max(int((cooldown_until_dt.astimezone(timezone.utc) - now).total_seconds()), 0)
        if seconds_left <= 0:
            continue
        cooldowns.append(
            ChannelCooldownItem(
                channel_username=str(row.get('channel_username', '')),
                cooldown_until=raw,
                seconds_left=seconds_left,
                consecutive_errors=int(row.get('consecutive_errors') or 0),
                last_error_code=(str(row['last_error_code']) if row.get('last_error_code') else None),
            )
        )

    events = [ChannelGuardEventItem(**row) for row in event_rows]
    return ChannelGuardStatusResponse(cooldowns=cooldowns, recent_events=events)


@router.get('/schedule', response_model=ScheduleSettings)
async def get_schedule(_user=Depends(require_user)) -> ScheduleSettings:
    payload = await get_setting('schedule')
    return ScheduleSettings(**payload)


@router.put('/schedule', response_model=ScheduleSettings)
async def update_schedule(payload: ScheduleSettings, _user=Depends(require_user)) -> ScheduleSettings:
    await set_setting('schedule', payload.model_dump())
    # Apply new interval without backend restart.
    try:
        from main import scheduler

        await scheduler.reload_from_settings()
    except Exception:
        # Keep settings update resilient even if runtime scheduler reload fails.
        pass
    return payload


@router.get('/skills', response_model=SkillsSettings)
async def get_skills(_user=Depends(require_user)) -> SkillsSettings:
    payload = await get_setting('skills')
    return SkillsSettings(**payload)


@router.put('/skills', response_model=SkillsSettings)
async def update_skills(payload: SkillsSettings, _user=Depends(require_user)) -> SkillsSettings:
    await set_setting('skills', payload.model_dump())
    return payload


@router.get('/memory', response_model=MemoryPreview)
async def get_memory_preview(_user=Depends(require_user)) -> MemoryPreview:
    base = Path('./backend/memory')
    return MemoryPreview(
        identity=(base / 'identity.md').read_text(encoding='utf-8') if (base / 'identity.md').exists() else '',
        sorting_rules=(base / 'sorting_rules.md').read_text(encoding='utf-8') if (base / 'sorting_rules.md').exists() else '',
        offers=(base / 'offers.md').read_text(encoding='utf-8') if (base / 'offers.md').exists() else '',
    )


@router.get('/userbot/config', response_model=UserbotConfigResponse)
async def get_userbot_config(_user=Depends(require_user)) -> UserbotConfigResponse:
    settings_payload = await get_setting('userbot')
    from core.config import get_settings as _get_settings

    env = _get_settings()
    api_id = int(settings_payload.get('api_id') or env.telethon_api_id or 0)
    stored_hash = str(settings_payload.get('api_hash') or '')
    if stored_hash:
        try:
            api_hash = decrypt_value(stored_hash)
        except ValueError:
            api_hash = ''
    else:
        api_hash = str(env.telethon_api_hash or '')
    session_name = normalize_session_name(
        str(settings_payload.get('session_name') or env.telethon_session or 'vaca_userbot'),
        default='vaca_userbot',
    )
    return UserbotConfigResponse(
        api_id=api_id,
        session_name=session_name,
        has_api_hash=bool(api_hash.strip()),
    )


@router.put('/userbot/config', response_model=UserbotConfigResponse)
async def update_userbot_config(
    payload: UserbotConfigUpdateRequest,
    _user=Depends(require_user),
) -> UserbotConfigResponse:
    existing = await get_setting('userbot')
    current_hash_encrypted = str(existing.get('api_hash') or '')
    if payload.api_hash is not None:
        plain_hash = payload.api_hash.strip()
        if plain_hash:
            try:
                api_hash_to_store = encrypt_value(plain_hash)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        else:
            api_hash_to_store = ''
    else:
        api_hash_to_store = current_hash_encrypted
        if api_hash_to_store and not api_hash_to_store.startswith('enc:v1:'):
            try:
                api_hash_to_store = encrypt_value(api_hash_to_store)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

    saved = {
        'api_id': int(payload.api_id),
        'api_hash': api_hash_to_store,
        'session_name': normalize_session_name(payload.session_name, default='vaca_userbot'),
    }
    await set_setting('userbot', saved)
    return UserbotConfigResponse(
        api_id=saved['api_id'],
        session_name=saved['session_name'],
        has_api_hash=bool(saved['api_hash']),
    )


@router.get('/userbot/status', response_model=UserbotStatusResponse)
async def get_userbot_status(_user=Depends(require_user)) -> UserbotStatusResponse:
    payload = await userbot_auth_service.status()
    return UserbotStatusResponse(**payload)


@router.post('/userbot/send-code', response_model=UserbotActionResponse)
async def send_userbot_code(
    payload: UserbotSendCodeRequest,
    _user=Depends(require_user),
) -> UserbotActionResponse:
    try:
        result = await userbot_auth_service.send_code(payload.phone)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UserbotActionResponse(**result)


@router.post('/userbot/sign-in', response_model=UserbotActionResponse)
async def sign_in_userbot(
    payload: UserbotSignInRequest,
    _user=Depends(require_user),
) -> UserbotActionResponse:
    try:
        result = await userbot_auth_service.sign_in(
            phone=payload.phone,
            code=payload.code,
            password=payload.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UserbotActionResponse(**result)


@router.post('/userbot/logout', response_model=UserbotActionResponse)
async def logout_userbot(_user=Depends(require_user)) -> UserbotActionResponse:
    try:
        result = await userbot_auth_service.logout()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UserbotActionResponse(**result)


@router.get('/userbot/channels', response_model=list[UserbotChannelItem])
async def list_userbot_channels(_user=Depends(require_user)) -> list[UserbotChannelItem]:
    try:
        items = await userbot_auth_service.list_channels()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [UserbotChannelItem(**item) for item in items]
