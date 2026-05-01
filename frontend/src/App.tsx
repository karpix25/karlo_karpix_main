import { useEffect, useState } from 'react';

import { NavTabs } from './components/NavTabs';
import { api } from './lib/api';
import { DraftReviewPage } from './pages/DraftReviewPage';
import { InboxPage } from './pages/InboxPage';
import { SettingsPage } from './pages/SettingsPage';
import './styles.css';

export default function App() {
  const [tab, setTab] = useState('inbox');
  const [accessDenied, setAccessDenied] = useState(false);
  const [checkingAccess, setCheckingAccess] = useState(true);

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

    const checkAccess = async () => {
      try {
        await api.getSources();
        setAccessDenied(false);
      } catch (e) {
        const message = (e as Error).message || '';
        setAccessDenied(message.includes('forbidden_for_user'));
      } finally {
        setCheckingAccess(false);
      }
    };
    void checkAccess();
  }, []);

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
      <header>
        <h1>VACA</h1>
        <p>Автономный контент-процесс для Carlo</p>
      </header>

      <NavTabs value={tab} onChange={setTab} />

      {tab === 'inbox' ? <InboxPage /> : null}
      {tab === 'drafts' ? <DraftReviewPage /> : null}
      {tab === 'settings' ? <SettingsPage /> : null}
    </main>
  );
}
