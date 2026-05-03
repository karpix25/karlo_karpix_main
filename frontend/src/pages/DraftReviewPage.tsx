import { useEffect, useMemo, useState } from 'react';

import { api } from '../lib/api';
import type { DraftItem, DraftPlatform } from '../types';

const platforms: { id: DraftPlatform; label: string }[] = [
  { id: 'telegram', label: 'Telegram' },
  { id: 'threads', label: 'Threads' },
  { id: '5s Reels', label: 'Reels' },
  { id: 'Аватар', label: 'Аватар' },
  { id: 'Карусель', label: 'Карусель' },
];

export function DraftReviewPage() {
  const [platform, setPlatform] = useState<DraftPlatform>('telegram');
  const [drafts, setDrafts] = useState<DraftItem[]>([]);
  const [selected, setSelected] = useState<DraftItem | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const selectedId = selected?.id;

  const load = async () => {
    setError('');
    try {
      const data = await api.getDrafts(platform, 'in_review');
      setDrafts(data);
      if (!selectedId && data.length) {
        setSelected(data[0]);
      }
      if (selectedId) {
        const refreshed = data.find((d) => d.id === selectedId);
        setSelected(refreshed ?? null);
      }
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    void load();
  }, [platform]);

  const contentPreview = useMemo(() => {
    if (!selected) return '';
    return `${selected.content}\n\nПризыв к действию: ${selected.cta || ''}\nХэштеги: ${selected.hashtags || ''}`;
  }, [selected]);

  const save = async () => {
    if (!selected) return;
    setBusy(true);
    setError('');
    try {
      const updated = await api.updateDraft(selected.id, {
        content: selected.content,
        cta: selected.cta,
        hashtags: selected.hashtags,
      });
      setSelected(updated);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const approve = async () => {
    if (!selected) return;
    setBusy(true);
    setError('');
    try {
      await api.approveDraft(selected.id);
      setSelected(null);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const reject = async () => {
    if (!selected) return;
    setBusy(true);
    setError('');
    try {
      await api.rejectDraft(selected.id);
      setSelected(null);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const regenerate = async () => {
    if (!selected) return;
    setBusy(true);
    setError('');
    try {
      const refreshed = await api.regenerateDraft(selected.id);
      setSelected(refreshed);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="app-content">
      <div className="toolbar" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '12px' }}>
        <h2>Проверка черновиков</h2>
        <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', width: '100%', paddingBottom: '4px' }}>
          {platforms.map((p) => (
            <button
              key={p.id}
              className={platform === p.id ? 'tab active' : 'tab'}
              onClick={() => setPlatform(p.id)}
              type="button"
              style={{ fontSize: '12px', padding: '8px 12px' }}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {error ? <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>{error}</div> : null}

      <div style={{ display: 'grid', gridTemplateColumns: drafts.length ? '250px 1fr' : '1fr', gap: '20px' }}>
        {drafts.length > 0 && (
          <div className="list">
            {drafts.map((draft) => (
              <button
                key={draft.id}
                className={selected?.id === draft.id ? 'card active' : 'card'}
                onClick={() => setSelected(draft)}
                type="button"
                style={{ padding: '12px', width: '100%', textAlign: 'left', display: 'block' }}
              >
                <div className="meta">Draft #{draft.id}</div>
                <p style={{ fontSize: '13px', margin: '4px 0 0', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {draft.content}
                </p>
              </button>
            ))}
          </div>
        )}

        {drafts.length === 0 && !busy && (
          <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
            <p style={{ color: 'var(--tg-hint)' }}>Нет черновиков для платформы {platform}.</p>
          </div>
        )}

        {selected && (
          <div className="editor card">
            <div style={{ marginBottom: '16px' }}>
              <label>Текст поста</label>
              <textarea
                value={selected.content}
                onChange={(e) => setSelected({ ...selected, content: e.target.value })}
                rows={8}
                style={{ fontSize: '14px', lineHeight: '1.6' }}
              />
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
              <div>
                <label>Призыв (CTA)</label>
                <input value={selected.cta || ''} onChange={(e) => setSelected({ ...selected, cta: e.target.value })} />
              </div>
              <div>
                <label>Хэштеги</label>
                <input
                  value={selected.hashtags || ''}
                  onChange={(e) => setSelected({ ...selected, hashtags: e.target.value })}
                />
              </div>
            </div>

            <div className="actions" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
              <button onClick={save} disabled={busy} type="button" style={{ background: 'rgba(0,0,0,0.05)', color: 'var(--text)' }}>
                Сохранить
              </button>
              <button onClick={regenerate} disabled={busy} type="button" style={{ background: 'rgba(0,0,0,0.05)', color: 'var(--text)' }}>
                Заново
              </button>
              <button onClick={approve} disabled={busy} type="button" style={{ background: 'var(--success)', color: 'white' }}>
                Одобрить
              </button>
              <button onClick={reject} disabled={busy} type="button" style={{ background: 'var(--danger)', color: 'white' }}>
                Отклонить
              </button>
            </div>
            
            <details style={{ marginTop: '20px' }}>
              <summary>Предпросмотр финала</summary>
              <pre style={{ marginTop: '8px' }}>{contentPreview}</pre>
            </details>
          </div>
        )}
      </div>
    </section>
  );
}

