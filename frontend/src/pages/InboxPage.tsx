import { useEffect, useState } from 'react';
import { motion, AnimatePresence, useMotionValue, useTransform } from 'framer-motion';

import { api, API_BASE } from '../lib/api';
import type { InboxItem } from '../types';

export function InboxPage() {
  const [items, setItems] = useState<InboxItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showFormatSelector, setShowFormatSelector] = useState<InboxItem | null>(null);
  const [decisionLoading, setDecisionLoading] = useState<Record<number, boolean>>({});

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getInbox('accepted');
      setItems(data);
      setCurrentIndex(0);
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
      setShowFormatSelector(null);
      // Move to next card
      setCurrentIndex(prev => prev + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setDecisionLoading(prev => ({ ...prev, [candidateId]: false }));
    }
  };

  const handleReject = async (candidateId: number) => {
    try {
      await api.rejectInboxItem(candidateId);
      setCurrentIndex(prev => prev + 1);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const currentItem = items[currentIndex];

  return (
    <section className="app-content" style={{ position: 'relative', height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
      <div className="toolbar" style={{ zIndex: 10 }}>
        <h2>Решение</h2>
        <button onClick={triggerRun} disabled={loading} type="button" style={{ width: 'auto' }}>
          {loading ? 'Загрузка...' : 'Запустить'}
        </button>
      </div>

      {error ? <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)', zIndex: 10 }}>⚠️ {error}</div> : null}

      <div className="swipe-container" style={{ position: 'relative', flex: 1, marginTop: '20px' }}>
        <AnimatePresence>
          {currentItem && !showFormatSelector && (
            <SwipeCard
              key={currentItem.candidate_id}
              item={currentItem}
              onSwipeLeft={() => handleReject(currentItem.candidate_id)}
              onSwipeRight={() => setShowFormatSelector(currentItem)}
            />
          )}
        </AnimatePresence>

        {!currentItem && !loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="card"
            style={{ textAlign: 'center', padding: '40px', marginTop: '40px' }}
          >
            <p style={{ color: 'var(--tg-hint)', fontSize: '18px', fontWeight: '500' }}>Все посты разобраны</p>
            <button onClick={load} style={{ marginTop: '20px', background: 'var(--field-bg)', color: 'var(--tg-text)' }}>
              Обновить список
            </button>
          </motion.div>
        )}
      </div>

      {showFormatSelector && (
        <motion.div
          initial={{ opacity: 0, y: 100 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 100 }}
          style={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            margin: '0 auto',
            width: '100%',
            maxWidth: '500px',
            background: 'var(--tg-secondary-bg)',
            padding: '24px 16px',
            borderTopLeftRadius: '24px',
            borderTopRightRadius: '24px',
            boxShadow: '0 -10px 40px rgba(0,0,0,0.3)',
            zIndex: 1000,
            boxSizing: 'border-box',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
            <h3 style={{ margin: 0 }}>Выбор формата</h3>
            <button onClick={() => setShowFormatSelector(null)} style={{ padding: '4px 8px', background: 'none', color: 'var(--tg-hint)', boxShadow: 'none', width: 'auto' }}>Закрыть</button>
          </div>
          <div className="actions" style={{ gridTemplateColumns: '1fr' }}>
            <button onClick={() => handleDecision(showFormatSelector.candidate_id, '5s Reels')} disabled={decisionLoading[showFormatSelector.candidate_id]}>
               5s Reels
            </button>
            <button onClick={() => handleDecision(showFormatSelector.candidate_id, 'Аватар')} disabled={decisionLoading[showFormatSelector.candidate_id]}>
               Аватар
            </button>
            <button onClick={() => handleDecision(showFormatSelector.candidate_id, 'Карусель')} disabled={decisionLoading[showFormatSelector.candidate_id]}>
               Карусель
            </button>
          </div>
        </motion.div>
      )}
    </section>
  );
}

function SwipeCard({ item, onSwipeLeft, onSwipeRight }: { item: InboxItem, onSwipeLeft: () => void, onSwipeRight: () => void }) {
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-200, 200], [-25, 25]);
  const opacity = useTransform(x, [-200, -150, 0, 150, 200], [0, 1, 1, 1, 0]);
  const nopeOpacity = useTransform(x, [-150, -50], [1, 0]);
  const likeOpacity = useTransform(x, [50, 150], [0, 1]);

  const handleDragEnd = (_: any, info: any) => {
    if (info.offset.x > 100) {
      onSwipeRight();
    } else if (info.offset.x < -100) {
      onSwipeLeft();
    }
  };

  return (
    <motion.div
      style={{
        x,
        rotate,
        position: 'absolute',
        width: 'calc(100% - 32px)',
        maxWidth: '400px',
        left: 0,
        right: 0,
        margin: '0 auto',
        cursor: 'grab',
        zIndex: 5,
      }}
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      onDragEnd={handleDragEnd}
      whileTap={{ cursor: 'grabbing' }}
      exit={{ x: x.get() < 0 ? '-150%' : '150%', opacity: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
    >
      <div className="card" style={{ height: '60vh', maxHeight: '600px', minHeight: '450px', display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: 0, boxShadow: '0 15px 35px rgba(0,0,0,0.2)' }}>
        <motion.div style={{ opacity: nopeOpacity, position: 'absolute', top: 40, right: 20, border: '4px solid var(--danger)', color: 'var(--danger)', padding: '8px 16px', borderRadius: '12px', fontWeight: 'bold', fontSize: '32px', zIndex: 10, transform: 'rotate(15deg)', pointerEvents: 'none' }}>
          NOPE
        </motion.div>
        <motion.div style={{ opacity: likeOpacity, position: 'absolute', top: 40, left: 20, border: '4px solid var(--success)', color: 'var(--success)', padding: '8px 16px', borderRadius: '12px', fontWeight: 'bold', fontSize: '32px', zIndex: 10, transform: 'rotate(-15deg)', pointerEvents: 'none' }}>
          LIKE
        </motion.div>


        {item.media_paths && item.media_paths.length > 0 ? (
          <div style={{ height: '240px', background: '#000', overflow: 'hidden' }}>
            {item.media_type === 'MessageMediaPhoto' ? (
              <img src={`${API_BASE}${item.media_paths[0]}`} alt="media" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <video src={`${API_BASE}${item.media_paths[0]}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            )}
          </div>
        ) : (
          <div style={{ height: '140px', background: 'var(--accent-gradient)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '48px' }}>
            📄
          </div>
        )}

        <div style={{ padding: '20px', flex: 1, overflowY: 'auto' }}>
          <div className="meta">
            <span>{item.channel_username}</span>
            <span style={{ marginLeft: 'auto', background: 'rgba(0,122,255,0.1)', color: 'var(--accent)', padding: '2px 8px', borderRadius: '4px' }}>
              Score: {item.relevance_score.toFixed(2)}
            </span>
          </div>
          <h3 style={{ margin: '12px 0 8px' }}>Краткое содержание</h3>
          <p style={{ fontSize: '15px', color: 'var(--tg-text)', lineHeight: '1.5' }}>{item.summary}</p>
          
          <details style={{ marginTop: '16px' }}>
            <summary>Полный текст</summary>
            <pre style={{ fontSize: '12px', marginTop: '8px' }}>{item.text}</pre>
          </details>
        </div>
        
        <div style={{ padding: '12px', textAlign: 'center', borderTop: '0.5px solid var(--separator)', color: 'var(--hint)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Свайп влево — Отклонить | Свайп вправо — Создать
        </div>
      </div>
    </motion.div>
  );
}

