import { useEffect, useState } from 'react';

import { api } from '../lib/api';
import type { DraftItem, DraftPlatform } from '../types';

const platforms: { id: DraftPlatform; label: string; icon: string }[] = [
  { id: 'telegram', label: 'Telegram', icon: '📱' },
  { id: 'telegraph', label: 'Telegra.ph', icon: '📝' },
  { id: 'digest', label: 'Дайджест', icon: '✨' },
  { id: 'threads', label: 'Threads', icon: '🧵' },
  { id: '5s Reels', label: 'Reels', icon: '🎬' },
  { id: 'Аватар', label: 'Аватар', icon: '👤' },
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
      } else if (selectedId) {
        const refreshed = data.find((d) => d.id === selectedId);
        setSelected(refreshed ?? (data.length ? data[0] : null));
      }
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    void load();
  }, [platform]);

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
      const updated = await api.regenerateDraft(selected.id);
      setSelected(updated);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="app-content" style={{ padding: '0 0 80px 0' }}>
      <div className="toolbar" style={{ 
        flexDirection: 'column', 
        alignItems: 'flex-start', 
        gap: '12px',
        padding: '20px',
        background: 'rgba(255,255,255,0.05)',
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <h2>Черновики</h2>
        <div className="platform-scroll" style={{ 
          display: 'flex', 
          gap: '8px', 
          overflowX: 'auto', 
          width: '100%', 
          paddingBottom: '8px',
          WebkitOverflowScrolling: 'touch'
        }}>
          {platforms.map((p) => (
            <button
              key={p.id}
              className={platform === p.id ? 'tab active' : 'tab'}
              onClick={() => setPlatform(p.id)}
              type="button"
              style={{ fontSize: '13px', whiteSpace: 'nowrap', display: 'flex', gap: '6px', alignItems: 'center' }}
            >
              <span>{p.icon}</span>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <div className="card" style={{ margin: '20px', borderColor: 'var(--danger)', color: 'var(--danger)' }}>
          {error}
        </div>
      ) : null}

      <div className="draft-layout-container" style={{ 
        display: 'flex', 
        flexDirection: 'column', // Stack by default for mobile
        gap: '0' 
      }}>
        <style>{`
          @media (min-width: 768px) {
            .draft-layout-container { flex-direction: row !important; }
            .draft-sidebar { width: 320px !important; border-right: 1px solid rgba(255,255,255,0.1) !important; border-bottom: none !important; }
            .draft-sidebar { height: calc(100vh - 160px) !important; overflow-y: auto; }
          }
        `}</style>

        {/* Sidebar / List */}
        <div className="draft-sidebar" style={{ 
          width: '100%',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
          padding: '12px',
          background: 'rgba(0,0,0,0.1)'
        }}>
          {drafts.length > 0 ? drafts.map((draft) => (
            <button
              key={draft.id}
              className={selected?.id === draft.id ? 'card active' : 'card'}
              onClick={() => setSelected(draft)}
              type="button"
              style={{ 
                padding: '12px', 
                width: '100%', 
                textAlign: 'left', 
                marginBottom: '8px',
                border: selected?.id === draft.id ? '1px solid var(--accent)' : '1px solid transparent',
                background: selected?.id === draft.id ? 'rgba(0,122,255,0.1)' : 'rgba(255,255,255,0.03)',
                boxShadow: 'none'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span className="meta" style={{ fontSize: '11px', opacity: 0.6 }}>ID {draft.id}</span>
                <span className="meta" style={{ fontSize: '11px', opacity: 0.6 }}>
                  {new Date(draft.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <p style={{ 
                fontSize: '13px', 
                margin: 0, 
                display: '-webkit-box', 
                WebkitLineClamp: 2, 
                WebkitBoxOrient: 'vertical', 
                overflow: 'hidden',
                lineHeight: '1.4',
                color: 'var(--text)'
              }}>
                {draft.content}
              </p>
            </button>
          )) : !busy && (
            <div style={{ textAlign: 'center', padding: '40px', opacity: 0.5 }}>
              <p>Пусто</p>
            </div>
          )}
        </div>

        {/* Main Editor Area */}
        <div className="draft-main" style={{ flex: 1, padding: '20px', minWidth: 0 }}>
          {selected ? (
            <div className="editor-container" style={{ maxWidth: '800px', margin: '0 auto' }}>
              <div style={{ marginBottom: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <label style={{ margin: 0 }}>Текст публикации</label>
                  <span className="meta" style={{ fontSize: '12px' }}>{selected.content.length} симв.</span>
                </div>
                <textarea
                  value={selected.content}
                  onChange={(e) => setSelected({ ...selected, content: e.target.value })}
                  rows={12}
                  style={{ 
                    fontSize: '16px', // Prevents iOS zoom
                    lineHeight: '1.5', 
                    background: 'rgba(255,255,255,0.05)',
                    padding: '16px',
                    borderRadius: '12px',
                    border: '1px solid rgba(255,255,255,0.1)',
                    width: '100%',
                    resize: 'none',
                    color: 'var(--text)'
                  }}
                />
              </div>
              
              <div style={{ marginBottom: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <label>Призыв (CTA)</label>
                  <input 
                    value={selected.cta || ''} 
                    onChange={(e) => setSelected({ ...selected, cta: e.target.value })}
                    style={{ background: 'rgba(255,255,255,0.05)', width: '100%' }}
                  />
                </div>
                <div>
                  <label>Хэштеги</label>
                  <input
                    value={selected.hashtags || ''}
                    onChange={(e) => setSelected({ ...selected, hashtags: e.target.value })}
                    style={{ background: 'rgba(255,255,255,0.05)', width: '100%' }}
                  />
                </div>
              </div>

              {/* Action Grid */}
              <div className="actions-grid" style={{ 
                display: 'grid', 
                gridTemplateColumns: '1fr 1fr', 
                gap: '10px' 
              }}>
                <button onClick={save} disabled={busy} type="button" style={{ 
                  background: 'rgba(255,255,255,0.1)', color: 'white', padding: '12px' 
                }}>
                  💾 Сохранить
                </button>
                <button onClick={regenerate} disabled={busy} type="button" style={{ 
                  background: 'rgba(255,255,255,0.1)', color: 'white', padding: '12px' 
                }}>
                  🔄 Заново
                </button>
                <button onClick={approve} disabled={busy} type="button" style={{ 
                  background: 'var(--success)', color: 'white', fontWeight: 'bold', padding: '12px', gridColumn: 'span 2' 
                }}>
                  🚀 Одобрить и Опубликовать
                </button>
                <button onClick={reject} disabled={busy} type="button" style={{ 
                  background: 'rgba(255,59,48,0.1)', color: 'var(--danger)', padding: '12px', gridColumn: 'span 2' 
                }}>
                  🗑️ Отклонить
                </button>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', height: '100%', minHeight: '200px', alignItems: 'center', justifyContent: 'center', opacity: 0.3 }}>
              <h3>Выберите черновик</h3>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
