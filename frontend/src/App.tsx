import { useEffect, useState } from 'react';

import { NavTabs } from './components/NavTabs';
import { api } from './lib/api';
import { DraftReviewPage } from './pages/DraftReviewPage';
import { InboxPage } from './pages/InboxPage';
import { SettingsPage } from './pages/SettingsPage';
import type { UserbotStatus } from './types';
import './styles.css';

const defaultUserbotStatus: UserbotStatus = {
  configured: false,
  authorized: false,
  session_name: '',
  requires_2fa: false,
};

export default function App() {
  const [tab, setTab] = useState('inbox');
  const [accessDenied, setAccessDenied] = useState(false);
  const [checkingAccess, setCheckingAccess] = useState(true);
  const [userbotStatus, setUserbotStatus] = useState<UserbotStatus>(defaultUserbotStatus);

  useEffect(() => {
    const webApp = (window as any)?.Telegram?.WebApp;
    if (webApp) {
      try {
        webApp.ready();
        webApp.expand();
      } catch {
        // noop
      }
    }

    const refreshUserbotStatus = async () => {
      try {
        const status = await api.getUserbotStatus();
        setUserbotStatus(status);
      } catch {
        // noop
      }
    };

    const checkAccess = async () => {
      try {
        await Promise.all([api.getSources(), refreshUserbotStatus()]);
        setAccessDenied(false);
      } catch (e) {
        const message = (e as Error).message || '';
        setAccessDenied(message.includes('forbidden_for_user'));
      } finally {
        setCheckingAccess(false);
      }
    };
    void checkAccess();

    const intervalId = window.setInterval(() => {
      void refreshUserbotStatus();
    }, 15000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, []);

  const statusBadge = (() => {
    if (!userbotStatus.configured) {
      return { text: 'Userbot не настроен', cls: 'warn' as const };
    }
    if (userbotStatus.authorized) {
      const account = userbotStatus.me_username ? ` · @${userbotStatus.me_username}` : '';
      return { text: `Userbot авторизован${account}`, cls: 'ok' as const };
    }
    if (userbotStatus.pending_phone) {
      return { text: 'Userbot ожидает код подтверждения', cls: 'warn' as const };
    }
    return { text: 'Userbot не авторизован', cls: 'bad' as const };
  })();

  if (checkingAccess) {
    return (
      <main className="app">
        <p>Проверка доступа...</p>
      </main>
    );
  }

  if (accessDenied) {
    return (
      <main className="app">
        <section className="card access-card">
          <h1>Доступ ограничен</h1>
          <p>Если вам нужна разработка контент автоматизации под ключ</p>
          <p>пишите мне @karlo25</p>
        </section>
      </main>
    );
  }

  return (
    <main className="app">
      <header className="app-header">
        <div className="app-header-row">
          <div className="app-brand">
            <h1>VACA</h1>
            <p>Автономный контент-процесс для Carlo</p>
          </div>
          <span className={`status-pill ${statusBadge.cls}`}>{statusBadge.text}</span>
        </div>
      </header>

      <section className="app-content">
        {tab === 'inbox' ? <InboxPage /> : null}
        {tab === 'drafts' ? <DraftReviewPage /> : null}
        {tab === 'settings' ? <SettingsPage /> : null}
      </section>

      <NavTabs value={tab} onChange={setTab} />
    </main>
  );
}
