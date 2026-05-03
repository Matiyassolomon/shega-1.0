/**
 * OneClickSave - Instant Like/Save with visual feedback
 * Single click action with animated confirmation
 * No confirmation dialogs, no extra steps
 */
import clsx from 'clsx';
import React, { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { LuBookmark, LuCheck, LuHeart } from 'react-icons/lu';
import { CgSpinnerTwo } from 'react-icons/cg';

import styles from './OneClickSave.module.css';

type SaveAction = 'like' | 'save' | 'both';

interface OneClickSaveProps {
  songId: string;
  initialLiked?: boolean;
  initialSaved?: boolean;
  action?: SaveAction;
  onLike?: (songId: string) => Promise<void>;
  onSave?: (songId: string) => Promise<void>;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

interface SaveState {
  liked: boolean;
  saved: boolean;
  loading: boolean;
  justClicked: boolean;
}

export const OneClickSave: React.FC<OneClickSaveProps> = ({
  songId,
  initialLiked = false,
  initialSaved = false,
  action = 'both',
  onLike,
  onSave,
  size = 'md',
  showLabel = false,
}) => {
  const { t } = useTranslation();
  const [state, setState] = useState<SaveState>({
    liked: initialLiked,
    saved: initialSaved,
    loading: false,
    justClicked: false,
  });

  useEffect(() => {
    setState(prev => ({
      ...prev,
      liked: initialLiked,
      saved: initialSaved,
    }));
  }, [initialLiked, initialSaved]);

  const sizeClasses = {
    sm: { button: styles.sm, icon: 14 },
    md: { button: styles.md, icon: 18 },
    lg: { button: styles.lg, icon: 24 },
  };

  const handleLike = useCallback(async () => {
    if (state.loading || !onLike) return;

    setState(prev => ({ ...prev, loading: true }));

    try {
      await onLike(songId);
      setState(prev => ({
        ...prev,
        liked: !prev.liked,
        loading: false,
        justClicked: true,
      }));

      // Reset justClicked animation after 1s
      setTimeout(() => {
        setState(prev => ({ ...prev, justClicked: false }));
      }, 1000);
    } catch {
      setState(prev => ({ ...prev, loading: false }));
    }
  }, [songId, onLike, state.loading]);

  const handleSave = useCallback(async () => {
    if (state.loading || !onSave) return;

    setState(prev => ({ ...prev, loading: true }));

    try {
      await onSave(songId);
      setState(prev => ({
        ...prev,
        saved: !prev.saved,
        loading: false,
        justClicked: true,
      }));

      setTimeout(() => {
        setState(prev => ({ ...prev, justClicked: false }));
      }, 1000);
    } catch {
      setState(prev => ({ ...prev, loading: false }));
    }
  }, [songId, onSave, state.loading]);

  // Single combined button for both actions
  if (action === 'both') {
    return (
      <div className={styles.group}>
        <button
          aria-label={state.liked ? t('common.unlike', 'Unlike') : t('common.like', 'Like')}
          onClick={handleLike}
          disabled={state.loading}
          className={clsx(
            styles.button,
            sizeClasses[size].button,
            state.liked ? styles.likeActive : styles.inactive,
            state.justClicked && state.liked && styles.pulse,
            state.loading && styles.loading,
          )}
          title={state.liked ? t('common.unlike', 'Unlike') : t('common.like', 'Like')}
        >
          {state.loading ? (
            <CgSpinnerTwo size={sizeClasses[size].icon} className={styles.spinner} />
          ) : state.liked ? (
            <LuHeart size={sizeClasses[size].icon} fill="currentColor" />
          ) : (
            <LuHeart size={sizeClasses[size].icon} />
          )}
        </button>

        <button
          aria-label={state.saved ? t('common.unsave', 'Unsave') : t('common.save', 'Save')}
          onClick={handleSave}
          disabled={state.loading}
          className={clsx(
            styles.button,
            sizeClasses[size].button,
            state.saved ? styles.saveActive : styles.inactive,
            state.justClicked && state.saved && styles.pulse,
            state.loading && styles.loading,
          )}
          title={state.saved ? t('common.unsave', 'Unsave') : t('common.save', 'Save')}
        >
          {state.loading ? (
            <CgSpinnerTwo size={sizeClasses[size].icon} className={styles.spinner} />
          ) : state.saved ? (
            <LuBookmark size={sizeClasses[size].icon} fill="currentColor" />
          ) : (
            <LuBookmark size={sizeClasses[size].icon} />
          )}
        </button>

        {state.justClicked && (
          <div className={styles.feedback}>
            <LuCheck size={16} />
          </div>
        )}
      </div>
    );
  }

  // Single action button
  const isLike = action === 'like';
  const isActive = isLike ? state.liked : state.saved;
  const handler = isLike ? handleLike : handleSave;

  return (
    <button
      aria-label={isLike ? t('common.like', 'Like') : t('common.save', 'Save')}
      onClick={handler}
      disabled={state.loading}
      className={clsx(
        styles.button,
        styles.withLabel,
        sizeClasses[size].button,
        isActive ? (isLike ? styles.likeActive : styles.saveActive) : styles.inactive,
        state.justClicked && styles.pulse,
        state.loading && styles.loading,
      )}
    >
      {state.loading ? (
        <CgSpinnerTwo size={sizeClasses[size].icon} className={styles.spinner} />
      ) : isActive ? (
        <>
          {isLike ? (
            <LuHeart size={sizeClasses[size].icon} fill="currentColor" />
          ) : (
            <LuBookmark size={sizeClasses[size].icon} fill="currentColor" />
          )}
          {showLabel && (
            <span>{isLike ? t('common.liked', 'Liked') : t('common.saved', 'Saved')}</span>
          )}
        </>
      ) : (
        <>
          {isLike ? <LuHeart size={sizeClasses[size].icon} /> : <LuBookmark size={sizeClasses[size].icon} />}
          {showLabel && (
            <span>{isLike ? t('common.like', 'Like') : t('common.save', 'Save')}</span>
          )}
        </>
      )}
    </button>
  );
};

export default OneClickSave;
