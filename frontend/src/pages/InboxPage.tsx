import { useEffect, useState } from 'react';

import { api, API_BASE } from '../lib/api';
import type { InboxItem } from '../types';

export function InboxPage() {
  const [items, setItems] = useState<InboxItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [decisionLoading, setDecisionLoading] = useState<Record<number, boolean>>({});

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

  const handleDecision = async (candidateId: number, format: string) => {
    setDecisionLoading(prev => ({ ...prev, [candidateId]: true }));
    setError('');
    try {
      await api.postDecision(candidateId, format);
      alert(`Сгенерирован формат: ${format}. Проверьте вкладку "Черновики".`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setDecisionLoading(prev => ({ ...prev, [candidateId]: false }));
    }
  };

  useEffect(() => {
    void load();
  }, []);

  return (
    <section className="app-content">
      <div className="toolbar">
        <h2>📥 Входящие материалы</h2>
        <button onClick={triggerRun} disabled={loading} type="button">
          {loading ? '⏳ Запуск...' : '🚀 Запустить пайплайн'}
        </button>
      </div>
      
      {error ? <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>⚠️ {error}</div> : null}
      
      <div className="list">
        {items.map((item) => (
          <article key={item.candidate_id} className="card">
            <div className="meta">
              <span>📡 {item.channel_username}</span>
              <span style={{ marginLeft: 'auto', background: 'color-mix(in srgb, var(--accent) 10%, transparent)', padding: '2px 8px', borderRadius: '4px' }}>
                ⭐️ {item.relevance_score.toFixed(2)}
              </span>
            </div>
            
            <p style={{ fontSize: '15px', fontWeight: '500', margin: '12px 0' }}>{item.summary}</p>
            
            <details>
              <summary>Посмотреть оригинал</summary>
              <div style={{ padding: '4px 0' }}>
                {item.media_paths && item.media_paths.length > 0 && (
                  <div className="media-preview" style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '8px' }}>
                    {item.media_paths.map((path, idx) => {
                       const url = `${API_BASE}${path}`;
                       return item.media_type === 'MessageMediaPhoto' 
                         ? <img key={idx} src={url} alt="media" style={{ maxHeight: '200px', borderRadius: '12px', flexShrink: 0 }} />
                         : <video key={idx} src={url} controls style={{ maxHeight: '200px', borderRadius: '12px', flexShrink: 0 }} />;
                    })}
                  </div>
                )}
                <pre>{item.text}</pre>
              </div>
            </details>
            
            <div className="actions">
               <button onClick={() => handleDecision(item.candidate_id, '5s Reels')} disabled={decisionLoading[item.candidate_id] || loading}>
                 🎥 5s Reels
               </button>
               <button onClick={() => handleDecision(item.candidate_id, 'Аватар')} disabled={decisionLoading[item.candidate_id] || loading}>
                 👤 Аватар
               </button>
               <button onClick={() => handleDecision(item.candidate_id, 'Карусель')} disabled={decisionLoading[item.candidate_id] || loading}>
                 📸 Карусель
               </button>
            </div>
          </article>
        ))}
        
        {!items.length && !loading ? (
          <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📦</div>
            <p style={{ color: 'var(--tg-hint)' }}>Пока нет входящих материалов.</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}
