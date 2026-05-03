import clsx from 'clsx';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { LuChevronDown, LuChevronUp } from 'react-icons/lu';

import styles from './SwipeablePlayerWrapper.module.css';

import { usePlayerStore } from '/@/renderer/store/player.store';

interface SwipeablePlayerWrapperProps {
    children: React.ReactNode;
    className?: string;
}

type SwipeDirection = 'up' | 'down' | null;

export const SwipeablePlayerWrapper: React.FC<SwipeablePlayerWrapperProps> = ({
    children,
    className = '',
}) => {
    const playerStore = usePlayerStore();
    const containerRef = useRef<HTMLDivElement>(null);
    const [swipeDirection, setSwipeDirection] = useState<SwipeDirection>(null);
    const [showHint, setShowHint] = useState(false);
    const [feedback, setFeedback] = useState<{ show: boolean; type: 'next' | 'previous' | null }>({
        show: false,
        type: null,
    });

    const touchState = useRef({
        isSwiping: false,
        startTime: 0,
        startY: 0,
    });

    const handleTouchStart = useCallback((e: React.TouchEvent) => {
        const touch = e.touches[0];

        touchState.current = {
            isSwiping: true,
            startTime: Date.now(),
            startY: touch.clientY,
        };
        setSwipeDirection(null);
    }, []);

    const handleTouchMove = useCallback((e: React.TouchEvent) => {
        if (!touchState.current.isSwiping) return;

        const touch = e.touches[0];
        const deltaY = touchState.current.startY - touch.clientY;
        const absDeltaY = Math.abs(deltaY);

        if (absDeltaY > 20 && absDeltaY < 100) {
            setSwipeDirection(deltaY > 0 ? 'up' : 'down');
        }

        if (absDeltaY > 10) {
            e.preventDefault();
        }
    }, []);

    const showSwipeFeedback = useCallback((type: 'next' | 'previous') => {
        setFeedback({ show: true, type });
        window.setTimeout(() => {
            setFeedback((prev) => ({ ...prev, show: false }));
        }, 600);
    }, []);

    const handleTouchEnd = useCallback(() => {
        if (!touchState.current.isSwiping) return;

        const deltaTime = Date.now() - touchState.current.startTime;
        touchState.current.isSwiping = false;

        if (deltaTime < 300 && swipeDirection) {
            if (swipeDirection === 'up') {
                playerStore.mediaNext();
                showSwipeFeedback('next');
            } else {
                playerStore.mediaPrevious();
                showSwipeFeedback('previous');
            }
        }

        setSwipeDirection(null);
    }, [playerStore, showSwipeFeedback, swipeDirection]);

    useEffect(() => {
        const timer = window.setTimeout(() => setShowHint(true), 1000);
        const hideTimer = window.setTimeout(() => setShowHint(false), 4000);

        return () => {
            window.clearTimeout(timer);
            window.clearTimeout(hideTimer);
        };
    }, []);

    return (
        <div
            ref={containerRef}
            className={clsx(styles.container, className)}
            onTouchEnd={handleTouchEnd}
            onTouchMove={handleTouchMove}
            onTouchStart={handleTouchStart}
        >
            {children}

            <AnimatePresence>
                {showHint && (
                    <>
                        <motion.div
                            animate={{ opacity: 0.6, y: 0 }}
                            className={clsx(styles.hint, styles.hintTop)}
                            exit={{ opacity: 0 }}
                            initial={{ opacity: 0, y: 20 }}
                        >
                            <LuChevronUp className={styles.bounce} size={32} />
                            <span>{'Swipe up for next'}</span>
                        </motion.div>
                        <motion.div
                            animate={{ opacity: 0.6, y: 0 }}
                            className={clsx(styles.hint, styles.hintBottom)}
                            exit={{ opacity: 0 }}
                            initial={{ opacity: 0, y: -20 }}
                        >
                            <span>{'Swipe down for previous'}</span>
                            <LuChevronDown className={styles.bounce} size={32} />
                        </motion.div>
                    </>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {swipeDirection && (
                    <motion.div
                        animate={{ opacity: 1, scale: 1 }}
                        className={clsx(
                            styles.preview,
                            swipeDirection === 'up' ? styles.previewTop : styles.previewBottom,
                        )}
                        exit={{ opacity: 0, scale: 0.9 }}
                        initial={{ opacity: 0, scale: 0.9 }}
                    >
                        <div className={styles.previewIcon}>
                            {swipeDirection === 'up' ? (
                                <LuChevronUp size={40} />
                            ) : (
                                <LuChevronDown size={40} />
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {feedback.show && (
                    <motion.div
                        animate={{ opacity: 1 }}
                        className={styles.feedbackOverlay}
                        exit={{ opacity: 0 }}
                        initial={{ opacity: 0 }}
                    >
                        <motion.div
                            animate={{ opacity: 1, scale: 1 }}
                            className={styles.feedback}
                            exit={{ opacity: 0, scale: 0.5 }}
                            initial={{ opacity: 0, scale: 0.5 }}
                        >
                            <p>{feedback.type === 'next' ? 'Next Track ->' : '<- Previous Track'}</p>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default SwipeablePlayerWrapper;
