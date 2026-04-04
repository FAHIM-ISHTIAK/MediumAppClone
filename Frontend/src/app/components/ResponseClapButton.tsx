import { useEffect, useState, useRef, useCallback } from 'react';
import { motion } from 'motion/react';
import { useApp } from '../context/AppContext';

interface ResponseClapButtonProps {
  articleId: string;
  responseId: string;
  initialClaps: number;
}

export default function ResponseClapButton({
  articleId,
  responseId,
  initialClaps,
}: ResponseClapButtonProps) {
  const { api, user } = useApp();
  const [isAnimating, setIsAnimating] = useState(false);
  const confirmedRef = useRef(initialClaps);
  const pendingRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const flushingRef = useRef(false);
  const [displayClaps, setDisplayClaps] = useState(initialClaps);

  useEffect(() => {
    confirmedRef.current = initialClaps;
    pendingRef.current = 0;
    setDisplayClaps(initialClaps);
  }, [initialClaps]);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  const updateDisplay = useCallback(() => {
    setDisplayClaps(confirmedRef.current + pendingRef.current);
  }, []);

  const flush = useCallback(async () => {
    if (!user || flushingRef.current) return;
    const count = pendingRef.current;
    if (count === 0) return;

    flushingRef.current = true;

    try {
      const res = await api.clapResponse(articleId, responseId, user.id, count);
      confirmedRef.current = res.likes;
      pendingRef.current = 0;
      updateDisplay();
    } catch (err) {
      pendingRef.current = 0;
      updateDisplay();
      console.error('Response clap failed:', err);
    } finally {
      flushingRef.current = false;
      if (pendingRef.current > 0) {
        flush();
      }
    }
  }, [api, articleId, responseId, user, updateDisplay]);

  const handleClap = () => {
    if (!user) return;

    setIsAnimating(true);
    setTimeout(() => setIsAnimating(false), 300);

    pendingRef.current += 1;
    updateDisplay();

    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(flush, 500);
  };

  return (
    <div className="flex items-center gap-1">
      <motion.button
        type="button"
        onClick={handleClap}
        className="relative inline-flex items-center gap-1 rounded-full px-2 py-1 transition-colors hover:bg-gray-100"
        whileTap={{ scale: 0.9 }}
        disabled={!user}
        title={user ? 'Clap this response' : 'Sign in to clap responses'}
      >
        <span>👏</span>
        {isAnimating && (
          <motion.div
            initial={{ opacity: 1, y: 0 }}
            animate={{ opacity: 0, y: -14 }}
            className="absolute -top-3 left-1/2 -translate-x-1/2 text-xs font-medium"
          >
            +1
          </motion.div>
        )}
      </motion.button>
      <span>{displayClaps > 0 ? displayClaps.toLocaleString() : 'Clap'}</span>
    </div>
  );
}
