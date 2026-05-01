import type {
  DraftItem,
  InboxItem,
  MemoryPreview,
  ScheduleSettings,
  SkillsSettings,
  SourcesSettings,
  UserbotActionResponse,
  UserbotChannelItem,
  UserbotConfig,
  UserbotStatus,
} from '../types';

const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? 'http://localhost:8000';

function telegramInitData(): string {
  const webApp = (window as any)?.Telegram?.WebApp;
  const fromTelegram = webApp?.initData;
  if (fromTelegram) return fromTelegram;
  if (import.meta.env.VITE_ALLOW_INSECURE_DEV === 'true') {
    return 'user_id=1&username=miniapp';
  }
  return '';
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': telegramInitData(),
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    try {
      const payload = JSON.parse(text) as { detail?: string };
      throw new Error(payload.detail || text || `HTTP ${response.status}`);
    } catch {
      throw new Error(text || `HTTP ${response.status}`);
    }
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  triggerRun: () => request<{ run_id: number; status: string }>('/api/runs/trigger', {
    method: 'POST',
    body: JSON.stringify({ trigger_source: 'manual' }),
  }),

  getInbox: (status = 'accepted') => request<InboxItem[]>(`/api/inbox?status=${encodeURIComponent(status)}`),

  getDrafts: (platform?: string, status?: string) => {
    const query = new URLSearchParams();
    if (platform) query.set('platform', platform);
    if (status) query.set('status', status);
    return request<DraftItem[]>(`/api/drafts?${query.toString()}`);
  },

  getDraft: (id: number) => request<DraftItem>(`/api/drafts/${id}`),

  updateDraft: (id: number, payload: { content: string; cta?: string; hashtags?: string }) =>
    request<DraftItem>(`/api/drafts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),

  approveDraft: (id: number) => request(`/api/drafts/${id}/approve`, { method: 'POST' }),
  rejectDraft: (id: number) => request(`/api/drafts/${id}/reject`, { method: 'POST' }),
  regenerateDraft: (id: number) => request<DraftItem>(`/api/drafts/${id}/regenerate`, { method: 'POST' }),

  getSources: () => request<SourcesSettings>('/api/settings/sources'),
  putSources: (payload: SourcesSettings) => request<SourcesSettings>('/api/settings/sources', {
    method: 'PUT',
    body: JSON.stringify(payload),
  }),

  getSchedule: () => request<ScheduleSettings>('/api/settings/schedule'),
  putSchedule: (payload: ScheduleSettings) => request<ScheduleSettings>('/api/settings/schedule', {
    method: 'PUT',
    body: JSON.stringify(payload),
  }),

  getSkills: () => request<SkillsSettings>('/api/settings/skills'),
  putSkills: (payload: SkillsSettings) => request<SkillsSettings>('/api/settings/skills', {
    method: 'PUT',
    body: JSON.stringify(payload),
  }),

  getMemory: () => request<MemoryPreview>('/api/settings/memory'),

  getUserbotStatus: () => request<UserbotStatus>('/api/settings/userbot/status'),
  getUserbotConfig: () => request<UserbotConfig>('/api/settings/userbot/config'),
  putUserbotConfig: (payload: { api_id: number; enabled: boolean; session_name: string; api_hash?: string | null }) =>
    request<UserbotConfig>('/api/settings/userbot/config', {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  sendUserbotCode: (phone: string) => request<UserbotActionResponse>('/api/settings/userbot/send-code', {
    method: 'POST',
    body: JSON.stringify({ phone }),
  }),
  signInUserbot: (payload: { phone: string; code?: string; password?: string }) =>
    request<UserbotActionResponse>('/api/settings/userbot/sign-in', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  logoutUserbot: () => request<UserbotActionResponse>('/api/settings/userbot/logout', { method: 'POST' }),
  getUserbotChannels: () => request<UserbotChannelItem[]>('/api/settings/userbot/channels'),
};
