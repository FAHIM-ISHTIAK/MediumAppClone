import { useState, useRef, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import { motion } from 'motion/react';

interface ClapButtonProps {
  articleId: string;
  initialClaps: number;
}

export default function ClapButton({ articleId, initialClaps }: ClapButtonProps) {
  const { api, user } = useApp();
  const [isAnimating, setIsAnimating] = useState(false);

  // confirmedClaps: the last value the server told us
  // pendingClaps: clicks accumulated since last server response
  const confirmedRef = useRef(initialClaps);
  const pendingRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const flushingRef = useRef(false);

  // displayed = confirmed + pending
  const [displayClaps, setDisplayClaps] = useState(initialClaps);

  const updateDisplay = useCallback(() => {
    setDisplayClaps(confirmedRef.current + pendingRef.current);
  }, []);

  const flush = useCallback(async () => {
    if (!user || flushingRef.current) return;
    const count = pendingRef.current;
    if (count === 0) return;

    flushingRef.current = true;

    try {
      const res = await api.clapArticle(articleId, user.id, count);
      // Server is the source of truth
      confirmedRef.current = res.totalClaps;
      // The pending claps we just sent are now confirmed
      pendingRef.current = 0;
      updateDisplay();
    } catch (err) {
      // Roll back the pending claps
      pendingRef.current = 0;
      updateDisplay();
      console.error('Clap failed:', err);
    } finally {
      flushingRef.current = false;
      // If more clicks arrived while flushing, flush again
      if (pendingRef.current > 0) {
        flush();
      }
    }
  }, [api, articleId, user, updateDisplay]);

  const handleClap = () => {
    if (!user) return;

    setIsAnimating(true);
    setTimeout(() => setIsAnimating(false), 300);

    // Optimistic: add to pending and update display
    pendingRef.current += 1;
    updateDisplay();

    // Debounce: wait 500ms after last click before sending to server
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(flush, 500);
  };

  return (
    <div className="flex items-center gap-2">
      <motion.button
        onClick={handleClap}
        className="relative p-2 hover:bg-gray-100 rounded-full transition-colors"
        whileTap={{ scale: 0.9 }}
        disabled={!user}
        title={user ? 'Clap' : 'Sign in to clap'}
      >
        <svg
          className="size-6"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M14 21L12 23L10 21M14 21C15.3968 21 16.7376 20.5819 17.889 19.8024C19.0404 19.0229 19.9506 17.9158 20.5065 16.6156C21.0624 15.3154 21.2399 13.8783 21.0173 12.4801C20.7947 11.0819 20.1818 9.78041 19.2518 8.73223M14 21H10M10 21C8.60322 21 7.26243 20.5819 6.11104 19.8024C4.95964 19.0229 4.04942 17.9158 3.49348 16.6156C2.93753 15.3154 2.76009 13.8783 2.98267 12.4801C3.20526 11.0819 3.81816 9.78041 4.74821 8.73223M4.74821 8.73223C5.67826 7.68405 6.88737 6.94549 8.22184 6.60739C9.55631 6.26929 10.9578 6.34447 12.2464 6.82479C13.535 7.30511 14.6547 8.17169 15.4669 9.31692C16.2792 10.4622 16.7498 11.8329 16.8214 13.2552M4.74821 8.73223L3 7M4.74821 8.73223L7 7"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill={isAnimating ? 'currentColor' : 'none'}
          />
        </svg>
        {isAnimating && (
          <motion.div
            initial={{ opacity: 1, y: 0 }}
            animate={{ opacity: 0, y: -20 }}
            className="absolute top-0 left-1/2 -translate-x-1/2 text-lg"
          >
            +1
          </motion.div>
        )}
      </motion.button>
      <span className="text-gray-600">{displayClaps.toLocaleString()}</span>
    </div>
  );
}
