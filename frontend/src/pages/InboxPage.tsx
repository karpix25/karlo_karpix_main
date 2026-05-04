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
  const [notice, setNotice] = useState('');

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
    setNotice('');
    try {
      await api.triggerRun();
      setNotice('Парсинг запущен. Новые посты появятся через несколько секунд.');
      setTimeout(() => setNotice(''), 5000);
      
      // Give the background worker a head start
      await new Promise(resolve => setTimeout(resolve, 1500));
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (candidateId: number, format: string) => {
    setDecisionLoading(prev => ({ ...prev, [candidateId]: true }));
    setError('');
    // Optimistic UI
    setCurrentIndex(prev => prev + 1);
    setShowFormatSelector(null);
    try {
      await api.postDecision(candidateId, format);
    } catch (e) {
      setError((e as Error).message);
      // Rollback on error
      setCurrentIndex(prev => prev - 1);
    } finally {
      setDecisionLoading(prev => ({ ...prev, [candidateId]: false }));
    }
  };

  const handleReject = async (candidateId: number) => {
    // Optimistic UI
    setCurrentIndex(prev => prev + 1);
    try {
      await api.rejectInboxItem(candidateId);
    } catch (e) {
      setError((e as Error).message);
      // Rollback on error
      setCurrentIndex(prev => prev - 1);
    }
  };

  const generateDigest = async () => {
    setLoading(true);
    setError('');
    try {
      await api.postDigest(24); // Default 24 hours
      setNotice('Дайджест успешно сформирован! Перейдите в раздел "Черновики".');
      setTimeout(() => setNotice(''), 5000);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
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
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={triggerRun} disabled={loading} type="button" style={{ width: 'auto' }}>
            {loading ? '⌛' : '📥 Поиск'}
          </button>
          <button onClick={generateDigest} disabled={loading} type="button" style={{ width: 'auto', background: 'rgba(0, 122, 255, 0.1)', color: 'var(--accent)' }}>
            ✨ Дайджест
          </button>
        </div>
      </div>

      {error ? <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)', zIndex: 10 }}>{error}</div> : null}
      {notice ? <div className="card" style={{ borderColor: 'var(--success)', color: 'var(--success)', zIndex: 10 }}>{notice}</div> : null}

      <div className="swipe-container" style={{ position: 'relative', flex: 1, marginTop: '20px' }}>
        <AnimatePresence initial={false}>
          {items.slice(currentIndex, currentIndex + 2).reverse().map((item, index, arr) => {
            const isTop = index === arr.length - 1;
            return (
              <SwipeCard
                key={item.candidate_id}
                item={item}
                isNext={!isTop}
                onSwipeLeft={isTop ? () => handleReject(item.candidate_id) : undefined}
                onSwipeRight={isTop ? () => setShowFormatSelector(item) : undefined}
              />
            );
          })}
        </AnimatePresence>

        {!currentItem && !loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="card"
            style={{ textAlign: 'center', padding: '40px', marginTop: '40px' }}
          >
            <p style={{ color: 'var(--hint)', fontSize: '18px', fontWeight: '500' }}>Все посты разобраны</p>
            <button onClick={load} style={{ marginTop: '20px', background: 'rgba(0,0,0,0.05)', color: 'var(--text)' }}>
              Обновить список
            </button>
          </motion.div>
        )}
      </div>

      {currentItem && !showFormatSelector && (
        <div className="action-buttons" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', padding: '16px 0', zIndex: 20 }}>
          <button 
            onClick={() => handleReject(currentItem.candidate_id)} 
            style={{ background: 'rgba(255, 59, 48, 0.1)', color: 'var(--danger)' }}
          >
            ❌ Отклонить
          </button>
          <button 
            onClick={() => setShowFormatSelector(currentItem)} 
            style={{ background: 'rgba(52, 199, 89, 0.1)', color: 'var(--success)' }}
          >
            ✅ В работу
          </button>
        </div>
      )}


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

function SwipeCard({ item, onSwipeLeft, onSwipeRight, isNext }: { item: InboxItem, onSwipeLeft?: () => void, onSwipeRight?: () => void, isNext?: boolean }) {
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-200, 200], [-25, 25]);
  const opacity = useTransform(x, [-200, -150, 0, 150, 200], [0, 1, 1, 1, 0]);
  const nopeOpacity = useTransform(x, [-150, -50], [1, 0]);
  const likeOpacity = useTransform(x, [50, 150], [0, 1]);

  const handleDragEnd = (_: any, info: any) => {
    const threshold = 80;
    if (info.offset.x > threshold) {
      onSwipeRight?.();
    } else if (info.offset.x < -threshold) {
      onSwipeLeft?.();
    }
  };

  return (
    <motion.div
      style={{
        x,
        rotate,
        position: 'absolute',
        width: 'calc(100% - 24px)',
        maxWidth: '400px',
        left: 0,
        right: 0,
        margin: '0 auto',
        cursor: isNext ? 'default' : 'grab',
        zIndex: isNext ? 1 : 5,
        touchAction: 'none',
        scale: isNext ? 0.95 : 1,
        y: isNext ? 15 : 0,
        opacity: isNext ? 0.5 : 1,
      }}
      drag={isNext ? false : "x"}
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={1}
      onDragEnd={handleDragEnd}
      whileTap={isNext ? {} : { cursor: 'grabbing' }}
      exit={{ x: x.get() < 0 ? '-200%' : '200%', opacity: 0 }}
      animate={{ scale: isNext ? 0.95 : 1, y: isNext ? 15 : 0, opacity: isNext ? 0.5 : 1 }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
    >
      <div className="card" style={{ height: '60vh', maxHeight: '600px', minHeight: '450px', display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: 0, boxShadow: '0 15px 35px rgba(0,0,0,0.2)' }}>
        <motion.div style={{ opacity: nopeOpacity, position: 'absolute', top: 40, right: 20, border: '4px solid var(--danger)', color: 'var(--danger)', padding: '8px 16px', borderRadius: '12px', fontWeight: 'bold', fontSize: '32px', zIndex: 10, transform: 'rotate(15deg)', pointerEvents: 'none' }}>
          NOPE
        </motion.div>
        <motion.div style={{ opacity: likeOpacity, position: 'absolute', top: 40, left: 20, border: '4px solid var(--success)', color: 'var(--success)', padding: '8px 16px', borderRadius: '12px', fontWeight: 'bold', fontSize: '32px', zIndex: 10, transform: 'rotate(-15deg)', pointerEvents: 'none' }}>
          LIKE
        </motion.div>


        {item.media_paths && item.media_paths.length > 0 ? (
          <div style={{ height: '260px', background: '#000', overflow: 'hidden' }}>
            {item.media_type === 'MessageMediaDocument' || item.media_type === 'Document' ? (
              <video src={item.media_paths[0].startsWith('/media') ? item.media_paths[0] : `${API_BASE}${item.media_paths[0]}`} controls={false} autoPlay loop muted style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <img src={item.media_paths[0].startsWith('/media') ? item.media_paths[0] : `${API_BASE}${item.media_paths[0]}`} alt="media" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            )}
          </div>
        ) : (
          <div style={{ height: '120px', background: 'var(--accent-gradient)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', color: 'rgba(255,255,255,0.8)', fontWeight: 500 }}>
            No visual attachment
          </div>
        )}

        <div style={{ padding: '20px', flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div className="meta" style={{ marginBottom: 0 }}>
            <span style={{ fontWeight: 600, color: 'var(--accent)' }}>{item.channel_username.replace('@', '')}</span>
            <span style={{ opacity: 0.6 }}>
              Match: {Math.round(item.relevance_score * 100)}%
            </span>
          </div>
          
          <h3 style={{ margin: '0 0 4px', fontSize: '20px', fontWeight: 700, lineHeight: '1.2' }}>
            {item.summary.split('\n')[0]}
          </h3>
          <p style={{ fontSize: '15px', color: 'var(--tg-text)', lineHeight: '1.4', opacity: 0.9, margin: 0, whiteSpace: 'pre-wrap' }}>
            {item.summary.split('\n').slice(1).join('\n').trim()}
          </p>
          
          <div style={{ marginTop: 'auto', paddingTop: '16px' }}>
            <details style={{ border: 'none', padding: 0 }}>
              <summary style={{ fontSize: '12px', opacity: 0.5, textTransform: 'uppercase', letterSpacing: '0.5px' }}>View Original</summary>
              <p style={{ fontSize: '14px', lineHeight: '1.45', marginTop: '12px', color: 'var(--tg-text)', whiteSpace: 'pre-wrap', opacity: 0.8 }}>
                {item.text}
              </p>
            </details>
          </div>
        </div>
        
        <div style={{ padding: '12px', textAlign: 'center', borderTop: '0.5px solid var(--separator)', color: 'var(--hint)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Свайп влево — Отклонить | Свайп вправо — Создать
        </div>
      </div>
    </motion.div>
  );
}

