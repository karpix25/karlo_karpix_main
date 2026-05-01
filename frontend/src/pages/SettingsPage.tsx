import { useEffect, useState } from 'react';

import { api } from '../lib/api';
import type {
  MemoryPreview,
  ScheduleSettings,
  SkillsSettings,
  SourcesSettings,
  UserbotChannelItem,
  UserbotConfig,
  UserbotStatus,
} from '../types';

const defaultUserbot: UserbotStatus = {
  configured: false,
  enabled: false,
  authorized: false,
  session_name: '',
  requires_2fa: false,
};

const defaultUserbotConfig: UserbotConfig = {
  api_id: 0,
  enabled: false,
  session_name: 'vaca_userbot',
  has_api_hash: false,
};

export function SettingsPage() {
  const [sources, setSources] = useState<SourcesSettings>({ channels: [] });
  const [schedule, setSchedule] = useState<ScheduleSettings>({ interval_minutes: 30 });
  const [skills, setSkills] = useState<SkillsSettings>({
    strict_links: true,
    ban_giveaways: true,
    prefer_technical_content: true,
  });
  const [memory, setMemory] = useState<MemoryPreview>({ identity: '', sorting_rules: '', offers: '' });
  const [userbot, setUserbot] = useState<UserbotStatus>(defaultUserbot);
  const [userbotConfig, setUserbotConfig] = useState<UserbotConfig>(defaultUserbotConfig);
  const [availableChannels, setAvailableChannels] = useState<UserbotChannelItem[]>([]);

  const [newChannel, setNewChannel] = useState('');
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [apiHashInput, setApiHashInput] = useState('');

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const addSourceChannel = (channelRaw: string) => {
    const channel = channelRaw.trim();
    if (!channel) return;
    const normalized = channel.startsWith('@') ? channel : `@${channel}`;
    const exists = sources.channels.some((item) => item.toLowerCase() === normalized.toLowerCase());
    if (!exists) {
      setSources({ channels: [...sources.channels, normalized] });
    }
  };

  const load = async () => {
    setError('');
    try {
      const [sourcesData, scheduleData, skillsData, memoryData, userbotStatus, userbotConfigData] = await Promise.all([
        api.getSources(),
        api.getSchedule(),
        api.getSkills(),
        api.getMemory(),
        api.getUserbotStatus(),
        api.getUserbotConfig(),
      ]);
      setSources(sourcesData);
      setSchedule(scheduleData);
      setSkills(skillsData);
      setMemory(memoryData);
      setUserbot(userbotStatus);
      setUserbotConfig(userbotConfigData);
      if (userbotStatus.pending_phone) {
        setPhone(userbotStatus.pending_phone);
      }
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const addChannel = () => {
    addSourceChannel(newChannel);
    setNewChannel('');
  };

  const saveAll = async () => {
    setError('');
    setBusy(true);
    try {
      await Promise.all([
        api.putSources(sources),
        api.putSchedule(schedule),
        api.putSkills(skills),
      ]);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const refreshUserbot = async () => {
    setError('');
    try {
      const [status, config] = await Promise.all([api.getUserbotStatus(), api.getUserbotConfig()]);
      setUserbot(status);
      setUserbotConfig(config);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const saveUserbotConfig = async () => {
    setError('');
    setBusy(true);
    try {
      await api.putUserbotConfig({
        api_id: userbotConfig.api_id,
        enabled: userbotConfig.enabled,
        session_name: userbotConfig.session_name,
        api_hash: apiHashInput.trim() ? apiHashInput.trim() : null,
      });
      setApiHashInput('');
      await refreshUserbot();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const sendCode = async () => {
    setError('');
    setBusy(true);
    try {
      await api.sendUserbotCode(phone);
      await refreshUserbot();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const signInByCode = async () => {
    setError('');
    setBusy(true);
    try {
      const result = await api.signInUserbot({ phone, code });
      if (result.requires_2fa) {
        setError('2FA password required. Enter account password and use Sign In With Password.');
      }
      await refreshUserbot();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const signInByPassword = async () => {
    setError('');
    setBusy(true);
    try {
      await api.signInUserbot({ phone, password });
      await refreshUserbot();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const logoutUserbot = async () => {
    setError('');
    setBusy(true);
    try {
      await api.logoutUserbot();
      setAvailableChannels([]);
      await refreshUserbot();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadChannelsFromUserbot = async () => {
    setError('');
    setBusy(true);
    try {
      const channels = await api.getUserbotChannels();
      setAvailableChannels(channels);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section>
      <div className="toolbar">
        <h2>Settings</h2>
        <button onClick={saveAll} disabled={busy} type="button">Save</button>
      </div>

      {error ? <p className="error">{error}</p> : null}

      <div className="card">
        <h3>Userbot Config</h3>
        <label>API ID</label>
        <input
          type="number"
          min={0}
          value={userbotConfig.api_id}
          onChange={(e) => setUserbotConfig({ ...userbotConfig, api_id: Number(e.target.value) })}
        />
        <label>API Hash</label>
        <input
          value={apiHashInput}
          onChange={(e) => setApiHashInput(e.target.value)}
          placeholder={userbotConfig.has_api_hash ? 'Saved. Enter only to replace.' : 'Enter API hash'}
          type="password"
        />
        <label>Session Name</label>
        <input
          value={userbotConfig.session_name}
          onChange={(e) => setUserbotConfig({ ...userbotConfig, session_name: e.target.value })}
          placeholder="vaca_userbot"
        />
        <label>
          <input
            type="checkbox"
            checked={userbotConfig.enabled}
            onChange={(e) => setUserbotConfig({ ...userbotConfig, enabled: e.target.checked })}
          />
          Enable Telethon runtime mode
        </label>
        <button onClick={saveUserbotConfig} disabled={busy} type="button">Save Userbot Config</button>
      </div>

      <div className="card">
        <h3>Userbot Auth</h3>
        <p className="meta">Configured: {userbot.configured ? 'yes' : 'no'} · Enabled in runtime: {userbotConfig.enabled ? 'yes' : 'no'}</p>
        <p className="meta">Authorized: {userbot.authorized ? 'yes' : 'no'} · Session: {userbot.session_name || '-'}</p>
        {userbot.me_username || userbot.me_phone ? (
          <p className="meta">Account: {userbot.me_username ? `@${userbot.me_username}` : '-'} {userbot.me_phone ? `(${userbot.me_phone})` : ''}</p>
        ) : null}

        <label>Phone (international format)</label>
        <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+1234567890" />

        <div className="actions auth-actions">
          <button onClick={sendCode} disabled={busy || !userbot.configured || !phone.trim()} type="button">Send Code</button>
          <button onClick={refreshUserbot} disabled={busy} type="button">Refresh Status</button>
          <button onClick={logoutUserbot} disabled={busy || !userbot.authorized} type="button">Logout</button>
        </div>

        <label>Code</label>
        <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="12345" />

        <label>2FA Password (if enabled)</label>
        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Telegram 2FA password"
          type="password"
        />

        <div className="actions auth-actions">
          <button onClick={signInByCode} disabled={busy || !phone.trim() || !code.trim()} type="button">Sign In With Code</button>
          <button onClick={signInByPassword} disabled={busy || !password.trim()} type="button">Sign In With Password</button>
        </div>

        {!userbot.configured ? (
          <p className="meta">Set TELETHON_API_ID and TELETHON_API_HASH in .env, then restart backend.</p>
        ) : null}
      </div>

      <div className="card">
        <h3>Source Channels</h3>
        <div className="inline">
          <input value={newChannel} onChange={(e) => setNewChannel(e.target.value)} placeholder="@channel" />
          <button onClick={addChannel} type="button">Add</button>
        </div>
        <ul>
          {sources.channels.map((channel) => (
            <li key={channel}>{channel}</li>
          ))}
        </ul>
      </div>

      <div className="card">
        <h3>Connect Channels From Userbot</h3>
        <button onClick={loadChannelsFromUserbot} disabled={busy || !userbot.authorized} type="button">Load My Channels</button>
        {!userbot.authorized ? <p className="meta">Authorize userbot first to fetch channel list.</p> : null}
        <div className="list compact-list">
          {availableChannels.map((channel) => (
            <article key={channel.id} className="card compact-card">
              <p><strong>{channel.title}</strong></p>
              <p className="meta">{channel.username}</p>
              <button
                onClick={() => addSourceChannel(channel.username)}
                type="button"
              >
                Add To Sources
              </button>
            </article>
          ))}
          {availableChannels.length === 0 ? <p className="meta">No channels loaded yet.</p> : null}
        </div>
      </div>

      <div className="card">
        <h3>Schedule</h3>
        <label>Interval Minutes</label>
        <input
          type="number"
          min={1}
          max={1440}
          value={schedule.interval_minutes}
          onChange={(e) => setSchedule({ interval_minutes: Number(e.target.value) })}
        />
      </div>

      <div className="card">
        <h3>Skill Toggles</h3>
        <label>
          <input
            type="checkbox"
            checked={skills.strict_links}
            onChange={(e) => setSkills({ ...skills, strict_links: e.target.checked })}
          />
          strict_links
        </label>
        <label>
          <input
            type="checkbox"
            checked={skills.ban_giveaways}
            onChange={(e) => setSkills({ ...skills, ban_giveaways: e.target.checked })}
          />
          ban_giveaways
        </label>
        <label>
          <input
            type="checkbox"
            checked={skills.prefer_technical_content}
            onChange={(e) => setSkills({ ...skills, prefer_technical_content: e.target.checked })}
          />
          prefer_technical_content
        </label>
      </div>

      <div className="card">
        <h3>Memory Preview</h3>
        <details>
          <summary>identity.md</summary>
          <pre>{memory.identity}</pre>
        </details>
        <details>
          <summary>sorting_rules.md</summary>
          <pre>{memory.sorting_rules}</pre>
        </details>
        <details>
          <summary>offers.md</summary>
          <pre>{memory.offers}</pre>
        </details>
      </div>
    </section>
  );
}
