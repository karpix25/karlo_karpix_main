from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from core.models import CandidateStatus, DraftPlatform, DraftStatus, RunStatus


class TriggerRunRequest(BaseModel):
    trigger_source: str = Field(default='manual')


class PipelineRunResponse(BaseModel):
    run_id: int
    status: RunStatus
    ingested_count: int
    candidates_count: int
    drafts_count: int


class InboxItem(BaseModel):
    candidate_id: int
    raw_message_id: int
    channel_username: str
    text: str
    summary: str
    relevance_score: float
    status: CandidateStatus
    reason: str | None
    created_at: datetime


class DraftItem(BaseModel):
    id: int
    candidate_id: int
    platform: DraftPlatform
    content: str
    cta: str | None
    hashtags: str | None
    status: DraftStatus
    publish_result: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime


class DraftUpdateRequest(BaseModel):
    content: str
    cta: str | None = None
    hashtags: str | None = None


class DraftActionResponse(BaseModel):
    id: int
    status: DraftStatus
    publish_result: str | None = None


class SourceSettings(BaseModel):
    channels: list[str]


class ScheduleSettings(BaseModel):
    interval_minutes: int = Field(ge=1, le=1440)


class SkillsSettings(BaseModel):
    strict_links: bool = True
    ban_giveaways: bool = True
    prefer_technical_content: bool = True


class MemoryPreview(BaseModel):
    identity: str
    sorting_rules: str
    offers: str


class SettingEnvelope(BaseModel):
    key: str
    value: dict[str, Any]


class UserbotStatusResponse(BaseModel):
    configured: bool
    enabled: bool
    authorized: bool
    session_name: str
    me_username: str | None = None
    me_phone: str | None = None
    requires_2fa: bool = False
    pending_phone: str | None = None
    pending_at: str | None = None


class UserbotSendCodeRequest(BaseModel):
    phone: str


class UserbotSignInRequest(BaseModel):
    phone: str
    code: str | None = None
    password: str | None = None


class UserbotActionResponse(BaseModel):
    status: str
    authorized: bool | None = None
    requires_2fa: bool | None = None
    me_username: str | None = None
    me_phone: str | None = None


class UserbotChannelItem(BaseModel):
    id: int
    title: str
    username: str


class UserbotConfigResponse(BaseModel):
    api_id: int
    enabled: bool
    session_name: str
    has_api_hash: bool


class UserbotConfigUpdateRequest(BaseModel):
    api_id: int = Field(ge=0)
    enabled: bool = False
    session_name: str = 'vaca_userbot'
    api_hash: str | None = None
