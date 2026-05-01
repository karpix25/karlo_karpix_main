export type CandidateStatus = 'accepted' | 'rejected';
export type DraftPlatform = 'telegram' | 'threads';
export type DraftStatus =
  | 'generated'
  | 'in_review'
  | 'approved'
  | 'published'
  | 'rejected'
  | 'ready_for_manual_publish'
  | 'error';

export interface InboxItem {
  candidate_id: number;
  raw_message_id: number;
  channel_username: string;
  text: string;
  summary: string;
  relevance_score: number;
  status: CandidateStatus;
  reason?: string;
  created_at: string;
}

export interface DraftItem {
  id: number;
  candidate_id: number;
  platform: DraftPlatform;
  content: string;
  cta?: string;
  hashtags?: string;
  status: DraftStatus;
  publish_result?: string;
  error?: string;
  created_at: string;
  updated_at: string;
}

export interface SourcesSettings {
  channels: string[];
}

export interface ScheduleSettings {
  interval_minutes: number;
}

export interface SkillsSettings {
  strict_links: boolean;
  ban_giveaways: boolean;
  prefer_technical_content: boolean;
}

export interface MemoryPreview {
  identity: string;
  sorting_rules: string;
  offers: string;
}

export interface UserbotStatus {
  configured: boolean;
  enabled: boolean;
  authorized: boolean;
  session_name: string;
  me_username?: string | null;
  me_phone?: string | null;
  requires_2fa: boolean;
  pending_phone?: string | null;
  pending_at?: string | null;
}

export interface UserbotActionResponse {
  status: string;
  authorized?: boolean | null;
  requires_2fa?: boolean | null;
  me_username?: string | null;
  me_phone?: string | null;
}

export interface UserbotChannelItem {
  id: number;
  title: string;
  username: string;
}

export interface UserbotConfig {
  api_id: number;
  enabled: boolean;
  session_name: string;
  has_api_hash: boolean;
}

export interface AntiAbuseSettings {
  enabled: boolean;
  messages_per_channel: number;
  channel_jitter_min_ms: number;
  channel_jitter_max_ms: number;
  batch_size: number;
  batch_pause_min_s: number;
  batch_pause_max_s: number;
  max_retries: number;
  retry_backoff_s: number[];
  floodwait_extra_jitter_min_s: number;
  floodwait_extra_jitter_max_s: number;
  channel_error_threshold: number;
  channel_cooldown_default_s: number;
  manual_bypass_cooldown: boolean;
}

export interface ChannelCooldownItem {
  channel_username: string;
  cooldown_until: string;
  seconds_left: number;
  consecutive_errors: number;
  last_error_code?: string | null;
}

export interface ChannelGuardEventItem {
  id: number;
  channel_username: string;
  event_type: string;
  event_payload: Record<string, unknown>;
  created_at: string;
}

export interface ChannelGuardStatus {
  cooldowns: ChannelCooldownItem[];
  recent_events: ChannelGuardEventItem[];
}
