import { useEffect, useState } from 'react';

import { api } from '../lib/api';
import type {
  AntiAbuseSettings,
  ChannelGuardStatus,
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
  authorized: false,
  session_name: '',
  requires_2fa: false,
};

const defaultUserbotConfig: UserbotConfig = {
  api_id: 0,
  session_name: 'vaca_userbot',
  has_api_hash: false,
};

const defaultAntiAbuse: AntiAbuseSettings = {
  enabled: true,
  messages_per_channel: 3,
  channel_jitter_min_ms: 1500,
  channel_jitter_max_ms: 4000,
  batch_size: 10,
  batch_pause_min_s: 15,
  batch_pause_max_s: 45,
  max_retries: 3,
  retry_backoff_s: [2, 8, 20],
  floodwait_extra_jitter_min_s: 1,
  floodwait_extra_jitter_max_s: 5,
  channel_error_threshold: 3,
  channel_cooldown_default_s: 1800,
  manual_bypass_cooldown: false,
};

const defaultGuardStatus: ChannelGuardStatus = {
  cooldowns: [],
  recent_events: [],
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
  const [antiAbuse, setAntiAbuse] = useState<AntiAbuseSettings>(defaultAntiAbuse);
  const [guardStatus, setGuardStatus] = useState<ChannelGuardStatus>(defaultGuardStatus);
  const [availableChannels, setAvailableChannels] = useState<UserbotChannelItem[]>([]);

  const [newChannel, setNewChannel] = useState('');
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [apiHashInput, setApiHashInput] = useState('');
  const [retryBackoffInput, setRetryBackoffInput] = useState('2,8,20');

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [activeTab, setActiveTab] = useState<'userbot' | 'sources' | 'ai' | 'system'>('userbot');

  const addSourceChannel = (channelRaw: string) => {
    const channel = channelRaw.trim();
    if (!channel) return;
    
    let normalized = channel;
    if (!normalized.startsWith('@') && !normalized.includes('/') && !normalized.startsWith('+')) {
      normalized = `@${normalized}`;
    }
    
    const exists = sources.channels.some((item) => item.toLowerCase() === normalized.toLowerCase());
    if (!exists) {
      setSources({ channels: [...sources.channels, normalized] });
    }
  };

  const load = async () => {
    setError('');
    try {
      const [
        sourcesData,
        scheduleData,
        skillsData,
        memoryData,
        userbotStatus,
        userbotConfigData,
        antiAbuseData,
        guardData,
      ] = await Promise.all([
        api.getSources(),
        api.getSchedule(),
        api.getSkills(),
        api.getMemory(),
        api.getUserbotStatus(),
        api.getUserbotConfig(),
        api.getAntiAbuse(),
        api.getGuardStatus(),
      ]);
      setSources(sourcesData);
      setSchedule(scheduleData);
      setSkills(skillsData);
      setMemory(memoryData);
      setUserbot(userbotStatus);
      setUserbotConfig(userbotConfigData);
      setAntiAbuse(antiAbuseData);
      setGuardStatus(guardData);
      setRetryBackoffInput(antiAbuseData.retry_backoff_s.join(','));
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
    setNotice('Канал добавлен. Не забудьте нажать "Сохранить всё".');
    setTimeout(() => setNotice(''), 3000);
  };

  const removeChannel = (channelToRemove: string) => {
    setSources({
      channels: sources.channels.filter((item) => item.toLowerCase() !== channelToRemove.toLowerCase()),
    });
  };

  const parseRetryBackoff = (): number[] => {
    const parsed = retryBackoffInput
      .split(',')
      .map((item) => Number(item.trim()))
      .filter((num) => Number.isFinite(num) && num >= 0);
    return parsed.length ? parsed : [2, 8, 20];
  };

  const saveAll = async () => {
    setError('');
    setNotice('');
    setBusy(true);
    try {
      const antiAbusePayload: AntiAbuseSettings = {
        ...antiAbuse,
        retry_backoff_s: parseRetryBackoff(),
      };
      await Promise.all([
        api.putSources(sources),
        api.putSchedule(schedule),
        api.putSkills(skills),
        api.putAntiAbuse(antiAbusePayload),
      ]);
      setNotice('Все настройки сохранены успешно!');
      setTimeout(() => setNotice(''), 4000);
      await load();
    } catch (e) {
      setError((e as Error).message);
      setTimeout(() => setError(''), 5000);
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
      setTimeout(() => setError(''), 5000);
    }
  };

  const refreshGuardStatus = async () => {
    setError('');
    try {
      const data = await api.getGuardStatus();
      setGuardStatus(data);
    } catch (e) {
      setError((e as Error).message);
      setTimeout(() => setError(''), 5000);
    }
  };

  const saveUserbotConfig = async () => {
    setError('');
    setNotice('');
    setBusy(true);
    try {
      await api.putUserbotConfig({
        api_id: userbotConfig.api_id,
        session_name: userbotConfig.session_name,
        api_hash: apiHashInput.trim() ? apiHashInput.trim() : null,
      });
      setApiHashInput('');
      setNotice('Конфиг userbot сохранен.');
      setTimeout(() => setNotice(''), 3000);
      await refreshUserbot();
    } catch (e) {
      setError((e as Error).message);
      setTimeout(() => setError(''), 5000);
    } finally {
      setBusy(false);
    }
  };

  const sendCode = async () => {
    setError('');
    setNotice('');
    setBusy(true);
    try {
      await api.sendUserbotCode(phone);
      setNotice('Код отправлен в Telegram.');
      setTimeout(() => setNotice(''), 5000);
      await refreshUserbot();
    } catch (e) {
      setError((e as Error).message);
      setTimeout(() => setError(''), 5000);
    } finally {
      setBusy(false);
    }
  };

  const signInByCode = async () => {
    setError('');
    setNotice('');
    setBusy(true);
    try {
      const result = await api.signInUserbot({ phone, code });
      if (result.requires_2fa) {
        setNotice('Введите пароль 2FA.');
      } else if (result.authorized) {
        setNotice('Вход выполнен успешно!');
      }
      setTimeout(() => setNotice(''), 4000);
      await refreshUserbot();
    } catch (e) {
      setError((e as Error).message);
      setTimeout(() => setError(''), 5000);
    } finally {
      setBusy(false);
    }
  };

  const signInByPassword = async () => {
    setError('');
    setNotice('');
    setBusy(true);
    try {
      const result = await api.signInUserbot({ phone, password });
      if (result.authorized) {
        setNotice('Вход по паролю успешен!');
      }
      setTimeout(() => setNotice(''), 4000);
      await refreshUserbot();
    } catch (e) {
      setError((e as Error).message);
      setTimeout(() => setError(''), 5000);
    } finally {
      setBusy(false);
    }
  };

  const logoutUserbot = async () => {
    setError('');
    setNotice('');
    setBusy(true);
    try {
      await api.logoutUserbot();
      setAvailableChannels([]);
      setNotice('Вы вышли из аккаунта.');
      setTimeout(() => setNotice(''), 3000);
      await refreshUserbot();
    } catch (e) {
      setError((e as Error).message);
      setTimeout(() => setError(''), 5000);
    } finally {
      setBusy(false);
    }
  };

  const loadChannelsFromUserbot = async () => {
    setError('');
    setNotice('');
    setBusy(true);
    try {
      const channels = await api.getUserbotChannels();
      setAvailableChannels(channels);
      setNotice(`Загружено каналов: ${channels.length}`);
      setTimeout(() => setNotice(''), 3000);
    } catch (e) {
      setError((e as Error).message);
      setTimeout(() => setError(''), 5000);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="app-content">
      {notice && <div className="notification-toast">{notice}</div>}
      {error && <div className="notification-toast error">{error}</div>}

      <div className="toolbar">
        <h2>Настройки</h2>
        <button onClick={saveAll} disabled={busy} type="button" style={{ width: 'auto' }}>
          {busy ? '...' : 'Сохранить всё'}
        </button>
      </div>

      <div className="settings-tabs">
        <button className={`tab ${activeTab === 'userbot' ? 'active' : ''}`} onClick={() => setActiveTab('userbot')}>Аккаунт</button>
        <button className={`tab ${activeTab === 'sources' ? 'active' : ''}`} onClick={() => setActiveTab('sources')}>Источники</button>
        <button className={`tab ${activeTab === 'ai' ? 'active' : ''}`} onClick={() => setActiveTab('ai')}>AI & Память</button>
        <button className={`tab ${activeTab === 'system' ? 'active' : ''}`} onClick={() => setActiveTab('system')}>Система</button>
      </div>

      {activeTab === 'userbot' && (
        <>
          <div className="card">
            <h3>Конфигурация Userbot</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label>API ID</label>
                <input
                  type="number"
                  min={0}
                  value={userbotConfig.api_id}
                  onChange={(e) => setUserbotConfig({ ...userbotConfig, api_id: Number(e.target.value) })}
                />
              </div>
              <div>
                <label>Имя сессии</label>
                <input
                  value={userbotConfig.session_name}
                  onChange={(e) => setUserbotConfig({ ...userbotConfig, session_name: e.target.value })}
                  placeholder="vaca_userbot"
                />
              </div>
            </div>
            <label>API Hash</label>
            <input
              value={apiHashInput}
              onChange={(e) => setApiHashInput(e.target.value)}
              placeholder={userbotConfig.has_api_hash ? 'Сохранён. Введите только для замены.' : 'Введите API hash'}
              type="password"
            />
            <button onClick={saveUserbotConfig} disabled={busy} type="button" style={{ background: 'rgba(0,0,0,0.05)', color: 'var(--text)' }}>
              Сохранить конфиг Userbot
            </button>
          </div>

          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3>Авторизация Userbot</h3>
              <span className={`status-pill ${userbot.authorized ? 'ok' : 'bad'}`}>
                {userbot.authorized ? 'АВТОРИЗОВАН' : 'НУЖЕН ВХОД'}
              </span>
            </div>
            
            <div style={{ background: 'var(--field-bg)', padding: '12px', borderRadius: '12px', marginBottom: '20px' }}>
              <p className="meta" style={{ margin: 0 }}>
                 {userbot.me_username ? `@${userbot.me_username}` : 'Аккаунт не подключен'} 
                 {userbot.me_phone ? ` · ${userbot.me_phone}` : ''}
              </p>
              <p className="meta" style={{ margin: '4px 0 0' }}>Сессия: {userbot.session_name || '-'}</p>
            </div>

            <label>Телефон (международный формат)</label>
            <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+1234567890" />

            <div className="actions" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '16px' }}>
              <button onClick={sendCode} disabled={busy || !userbot.configured || !phone.trim()} type="button" style={{ fontSize: '12px' }}>
                Код
              </button>
              <button onClick={refreshUserbot} disabled={busy} type="button" style={{ fontSize: '12px', background: 'rgba(0,0,0,0.05)', color: 'var(--text)' }}>
                Обновить
              </button>
              <button onClick={logoutUserbot} disabled={busy || !userbot.authorized} type="button" style={{ fontSize: '12px', background: 'var(--danger)', color: 'white' }}>
                Выйти
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '12px' }}>
              <div>
                <label>Код</label>
                <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="12345" />
              </div>
              <div>
                <label>Пароль 2FA</label>
                <input
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Если включён"
                  type="password"
                />
              </div>
            </div>

            <div className="actions" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <button onClick={signInByCode} disabled={busy || !phone.trim() || !code.trim()} type="button">
                Войти по коду
              </button>
              <button onClick={signInByPassword} disabled={busy || !password.trim()} type="button">
                По паролю
              </button>
            </div>
          </div>
          
          <div className="card">
            <h3>Подключение каналов из Userbot</h3>
            <button onClick={loadChannelsFromUserbot} disabled={busy || !userbot.authorized} type="button">Загрузить мои каналы</button>
            {!userbot.authorized ? <p className="meta">Сначала авторизуйте userbot, чтобы получить список каналов.</p> : null}
            <div className="list compact-list">
              {availableChannels.map((channel) => (
                <article key={channel.id} className="card compact-card">
                  <p><strong>{channel.title}</strong></p>
                  <p className="meta">{channel.username}</p>
                  <button
                    onClick={() => addSourceChannel(channel.username)}
                    type="button"
                  >
                    Добавить в источники
                  </button>
                </article>
              ))}
              {availableChannels.length === 0 ? <p className="meta">Каналы пока не загружены.</p> : null}
            </div>
          </div>
        </>
      )}

      {activeTab === 'sources' && (
        <div className="card">
          <h3>Каналы-источники</h3>
          <div className="inline">
            <input value={newChannel} onChange={(e) => setNewChannel(e.target.value)} placeholder="@username или ссылка-приглашение" />
            <button onClick={addChannel} type="button">Добавить</button>
          </div>
          <ul className="channel-list">
            {sources.channels.map((channel) => (
              <li key={channel}>
                <span>{channel}</span>
                <button type="button" className="danger-inline" onClick={() => removeChannel(channel)}>Удалить</button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {activeTab === 'ai' && (
        <>
          <div className="card">
            <h3>Тогглы правил</h3>
            <label>
              <input
                type="checkbox"
                checked={skills.strict_links}
                onChange={(e) => setSkills({ ...skills, strict_links: e.target.checked })}
              />
              Строгая проверка ссылок (strict_links)
            </label>
            <label>
              <input
                type="checkbox"
                checked={skills.ban_giveaways}
                onChange={(e) => setSkills({ ...skills, ban_giveaways: e.target.checked })}
              />
              Блокировать giveaway/промо (ban_giveaways)
            </label>
            <label>
              <input
                type="checkbox"
                checked={skills.prefer_technical_content}
                onChange={(e) => setSkills({ ...skills, prefer_technical_content: e.target.checked })}
              />
              Предпочитать технический контент (prefer_technical_content)
            </label>
          </div>

          <div className="card">
            <h3>Предпросмотр памяти</h3>
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
        </>
      )}

      {activeTab === 'system' && (
        <>
          <div className="card">
            <h3>Расписание</h3>
            <label>Интервал (минуты)</label>
            <input
              type="number"
              min={1}
              max={1440}
              value={schedule.interval_minutes}
              onChange={(e) => setSchedule({ interval_minutes: Number(e.target.value) })}
            />
          </div>

          <div className="card">
            <h3>Антибан-настройки</h3>
            <label>
              <input
                type="checkbox"
                checked={antiAbuse.enabled}
                onChange={(e) => setAntiAbuse({ ...antiAbuse, enabled: e.target.checked })}
              />
              Включить anti-ban защиту
            </label>
            <details>
              <summary>Показать расширенные параметры</summary>
              <div style={{ marginTop: '12px' }}>
                <label>Сообщений на канал</label>
                <input
                  type="number"
                  min={1}
                  value={antiAbuse.messages_per_channel}
                  onChange={(e) => setAntiAbuse({ ...antiAbuse, messages_per_channel: Number(e.target.value) })}
                />
                <label>Максимум повторов</label>
                <input
                  type="number"
                  min={0}
                  value={antiAbuse.max_retries}
                  onChange={(e) => setAntiAbuse({ ...antiAbuse, max_retries: Number(e.target.value) })}
                />
                <label>Порог ошибок канала</label>
                <input
                  type="number"
                  min={1}
                  value={antiAbuse.channel_error_threshold}
                  onChange={(e) => setAntiAbuse({ ...antiAbuse, channel_error_threshold: Number(e.target.value) })}
                />
              </div>
            </details>
          </div>

          <div className="card">
            <div className="toolbar">
              <h3>Статус защиты каналов</h3>
              <button onClick={refreshGuardStatus} type="button" style={{ width: 'auto' }}>Обновить</button>
            </div>
            <p className="meta">Каналы в cooldown: {guardStatus.cooldowns.length}</p>
            {guardStatus.cooldowns.length > 0 && (
              <details>
                <summary>Список каналов</summary>
                <div className="list compact-list" style={{ marginTop: '12px' }}>
                  {guardStatus.cooldowns.map((item) => (
                    <article key={item.channel_username} className="card compact-card">
                      <p><strong>{item.channel_username}</strong></p>
                      <p className="meta">осталось сек: {item.seconds_left} · ошибок: {item.consecutive_errors}</p>
                    </article>
                  ))}
                </div>
              </details>
            )}
          </div>
        </>
      )}
    </section>
  );

}
