/**
 * Swipe Navigation Hook
 * Provides touch gesture support for player navigation
 * Swipe UP = Next track
 * Swipe DOWN = Previous track
 */
import { useCallback, useRef } from 'react';

interface SwipeOptions {
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  threshold?: number;
  preventDefault?: boolean;
}

interface SwipeState {
  startY: number;
  startTime: number;
  isSwiping: boolean;
}

export const useSwipeNavigation = (options: SwipeOptions) => {
  const { onSwipeUp, onSwipeDown, threshold = 50, preventDefault = true } = options;
  const swipeState = useRef<SwipeState>({
    startY: 0,
    startTime: 0,
    isSwiping: false,
  });

  const handleTouchStart = useCallback(
    (e: TouchEvent) => {
      const touch = e.touches[0];
      swipeState.current = {
        startY: touch.clientY,
        startTime: Date.now(),
        isSwiping: true,
      };
    },
    []
  );

  const handleTouchMove = useCallback(
    (e: TouchEvent) => {
      if (!swipeState.current.isSwiping) return;

      const touch = e.touches[0];
      const deltaY = swipeState.current.startY - touch.clientY;
      const absDeltaY = Math.abs(deltaY);

      // Prevent default only for vertical swipes to allow horizontal scrolling
      if (preventDefault && absDeltaY > 10) {
        e.preventDefault();
      }
    },
    [preventDefault]
  );

  const handleTouchEnd = useCallback(
    (e: TouchEvent) => {
      if (!swipeState.current.isSwiping) return;

      const touch = e.changedTouches[0];
      const deltaY = swipeState.current.startY - touch.clientY;
      const deltaTime = Date.now() - swipeState.current.startTime;
      const absDeltaY = Math.abs(deltaY);

      // Only trigger if swipe is fast enough (less than 300ms) and exceeds threshold
      if (deltaTime < 300 && absDeltaY > threshold) {
        if (deltaY > 0) {
          // Swiped UP (startY > endY) = Next track
          onSwipeUp?.();
        } else {
          // Swiped DOWN (startY < endY) = Previous track
          onSwipeDown?.();
        }
      }

      swipeState.current.isSwiping = false;
    },
    [onSwipeUp, onSwipeDown, threshold]
  );

  const bindSwipe = useCallback(
    (element: HTMLElement | null) => {
      if (!element) return;

      element.addEventListener('touchstart', handleTouchStart, { passive: true });
      element.addEventListener('touchmove', handleTouchMove, { passive: false });
      element.addEventListener('touchend', handleTouchEnd, { passive: true });

      return () => {
        element.removeEventListener('touchstart', handleTouchStart);
        element.removeEventListener('touchmove', handleTouchMove);
        element.removeEventListener('touchend', handleTouchEnd);
      };
    },
    [handleTouchStart, handleTouchMove, handleTouchEnd]
  );

  return { bindSwipe };
};

// Hook for player component that directly connects to player store
export const usePlayerSwipeNavigation = (playerActions: {
  mediaNext: () => void;
  mediaPrevious: () => void;
}) => {
  const { bindSwipe } = useSwipeNavigation({
    onSwipeUp: () => {
      playerActions.mediaNext();
    },
    onSwipeDown: () => {
      playerActions.mediaPrevious();
    },
  });

  return { bindSwipe };
};

export default useSwipeNavigation;
