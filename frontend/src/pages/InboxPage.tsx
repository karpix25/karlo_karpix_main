import { useEffect, useState } from 'react';

import { api } from '../lib/api';
import type { InboxItem } from '../types';

export function InboxPage() {
  const [items, setItems] = useState<InboxItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getInbox('accepted');
      setItems(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const triggerRun = async () => {
    setLoading(true);
    setError('');
    try {
      await api.triggerRun();
      await load();
    } catch (e) {
      setError((e as Error).message);
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  return (
    <section>
      <div className="toolbar">
        <h2>Входящие</h2>
        <button onClick={triggerRun} disabled={loading} type="button">
          {loading ? 'Запуск...' : 'Запустить пайплайн'}
        </button>
      </div>
      {error ? <p className="error">{error}</p> : null}
      <div className="list">
        {items.map((item) => (
          <article key={item.candidate_id} className="card">
            <p className="meta">{item.channel_username} · релевантность {item.relevance_score.toFixed(2)}</p>
            <p>{item.summary}</p>
            <details>
              <summary>Текст источника</summary>
              <pre>{item.text}</pre>
            </details>
          </article>
        ))}
        {!items.length && !loading ? <p>Пока нет входящих материалов.</p> : null}
      </div>
    </section>
  );
}
