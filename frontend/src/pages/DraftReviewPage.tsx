import { useEffect, useMemo, useState } from 'react';

import { api } from '../lib/api';
import type { DraftItem, DraftPlatform } from '../types';

export function DraftReviewPage() {
  const [platform, setPlatform] = useState<DraftPlatform>('telegram');
  const [drafts, setDrafts] = useState<DraftItem[]>([]);
  const [selected, setSelected] = useState<DraftItem | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const selectedId = selected?.id;

  const load = async () => {
    setError('');
    const data = await api.getDrafts(platform, 'in_review');
    setDrafts(data);
    if (!selectedId && data.length) {
      setSelected(data[0]);
    }
    if (selectedId) {
      const refreshed = data.find((d) => d.id === selectedId);
      setSelected(refreshed ?? null);
    }
  };

  useEffect(() => {
    void load().catch((e: Error) => setError(e.message));
  }, [platform]);

  const contentPreview = useMemo(() => {
    if (!selected) return '';
    return `${selected.content}\n\nCTA: ${selected.cta || ''}\nHashtags: ${selected.hashtags || ''}`;
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
    <section>
      <div className="toolbar">
        <h2>Draft Review</h2>
        <div className="tabs small">
          <button className={platform === 'telegram' ? 'tab active' : 'tab'} onClick={() => setPlatform('telegram')} type="button">
            Telegram
          </button>
          <button className={platform === 'threads' ? 'tab active' : 'tab'} onClick={() => setPlatform('threads')} type="button">
            Threads
          </button>
        </div>
      </div>

      {error ? <p className="error">{error}</p> : null}

      <div className="split">
        <div className="list">
          {drafts.map((draft) => (
            <button
              key={draft.id}
              className={selected?.id === draft.id ? 'card active' : 'card'}
              onClick={() => setSelected(draft)}
              type="button"
            >
              <p className="meta">Draft #{draft.id}</p>
              <p>{draft.content.slice(0, 120)}...</p>
            </button>
          ))}
          {!drafts.length ? <p>No drafts in review.</p> : null}
        </div>

        <div className="editor">
          {selected ? (
            <>
              <label>Content</label>
              <textarea
                value={selected.content}
                onChange={(e) => setSelected({ ...selected, content: e.target.value })}
                rows={10}
              />
              <label>CTA</label>
              <input value={selected.cta || ''} onChange={(e) => setSelected({ ...selected, cta: e.target.value })} />
              <label>Hashtags</label>
              <input
                value={selected.hashtags || ''}
                onChange={(e) => setSelected({ ...selected, hashtags: e.target.value })}
              />
              <div className="actions">
                <button onClick={save} disabled={busy} type="button">Save</button>
                <button onClick={regenerate} disabled={busy} type="button">Regenerate</button>
                <button onClick={approve} disabled={busy} type="button">Approve</button>
                <button onClick={reject} disabled={busy} type="button">Reject</button>
              </div>
              <pre className="preview">{contentPreview}</pre>
            </>
          ) : (
            <p>Select a draft.</p>
          )}
        </div>
      </div>
    </section>
  );
}
