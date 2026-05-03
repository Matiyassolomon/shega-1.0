/**
 * QuickPlaylistModal - 3-Step Playlist Creation
 * Step 1: Enter name
 * Step 2: Select privacy (Public/Private)
 * Step 3: Done
 */
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { CgSpinnerTwo } from 'react-icons/cg';
import { LuCheck, LuGlobe, LuListMusic, LuLock, LuX } from 'react-icons/lu';

import styles from './QuickModal.module.css';

interface QuickPlaylistModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (name: string, isPublic: boolean) => Promise<void>;
  initialSongs?: string[];
}

type PlaylistStep = 'name' | 'privacy' | 'success';

export const QuickPlaylistModal: React.FC<QuickPlaylistModalProps> = ({
  isOpen,
  onClose,
  onCreate,
  initialSongs = [],
}) => {
  const { t } = useTranslation();
  const [step, setStep] = useState<PlaylistStep>('name');
  const [name, setName] = useState('');
  const [isPublic, setIsPublic] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleNameSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      setError(null);
      setStep('privacy');
    }
  };

  const handleCreate = async () => {
    setIsCreating(true);
    setError(null);
    try {
      await onCreate(name.trim(), isPublic);
      setStep('success');
    } catch (error) {
      setError(error instanceof Error ? error.message : t('playlist.createFailed', 'Could not create playlist. Please try again.'));
    } finally {
      setIsCreating(false);
    }
  };

  const handleClose = () => {
    setStep('name');
    setName('');
    setIsPublic(true);
    setError(null);
    onClose();
  };

  return (
    <div className={styles.overlay} role="dialog" aria-modal="true">
      <div className={styles.panel}>
        <div className={styles.header}>
          <h2 className={styles.titleWithIcon}>
            <LuListMusic size={20} />
            {step === 'name' && t('playlist.create', 'New Playlist')}
            {step === 'privacy' && t('playlist.privacy', 'Privacy')}
            {step === 'success' && t('playlist.created', 'Created!')}
          </h2>
          <button
            aria-label={t('common.close', 'Close')}
            onClick={handleClose}
            className={styles.iconButton}
          >
            <LuX size={20} />
          </button>
        </div>

        {step === 'name' && (
          <form onSubmit={handleNameSubmit} className={styles.body}>
            <div>
              <label className={styles.label}>
                {t('playlist.name', 'Playlist Name')}
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t('playlist.placeholder', 'My Awesome Playlist')}
                className={styles.input}
                autoFocus
              />
            </div>
            {initialSongs.length > 0 && (
              <p className={styles.muted}>
                {t('playlist.willAddSongs', 'Will add {{count}} songs', { count: initialSongs.length })}
              </p>
            )}
            <button
              type="submit"
              disabled={!name.trim()}
              className={styles.primaryButton}
            >
              {t('common.next', 'Next')}
            </button>
          </form>
        )}

        {step === 'privacy' && (
          <div className={styles.body}>
            <p className={styles.muted}>
              {t('playlist.selectPrivacy', 'Who can see this?')}
            </p>
            <button
              onClick={() => setIsPublic(true)}
              className={`${styles.option} ${isPublic ? styles.selectedOption : ''}`}
            >
              <LuGlobe size={24} />
              <div className={styles.optionText}>
                <p>{t('playlist.public', 'Public')}</p>
                <span>{t('playlist.publicDesc', 'Everyone can see')}</span>
              </div>
            </button>
            <button
              onClick={() => setIsPublic(false)}
              className={`${styles.option} ${!isPublic ? styles.selectedOption : ''}`}
            >
              <LuLock size={24} />
              <div className={styles.optionText}>
                <p>{t('playlist.private', 'Private')}</p>
                <span>{t('playlist.privateDesc', 'Only you')}</span>
              </div>
            </button>
            {error && <p className={styles.error}>{error}</p>}
            <div className={styles.buttonRow}>
              <button
                onClick={() => setStep('name')}
                className={styles.secondaryButton}
              >
                {t('common.back', 'Back')}
              </button>
              <button
                onClick={handleCreate}
                disabled={isCreating}
                className={styles.primaryButton}
              >
                {isCreating ? (
                  <CgSpinnerTwo size={18} className={styles.spinner} />
                ) : (
                  t('playlist.createBtn', 'Create')
                )}
              </button>
            </div>
          </div>
        )}

        {step === 'success' && (
          <div className={styles.bodySuccess}>
            <div className={styles.successIcon}>
              <LuCheck size={40} />
            </div>
            <div>
              <h3 className={styles.successTitle}>"{name}"</h3>
              <p className={styles.muted}>{t('playlist.createdSuccess', 'Playlist created!')}</p>
            </div>
            <button
              onClick={handleClose}
              className={styles.primaryButton}
            >
              {t('common.done', 'Done')}
            </button>
          </div>
        )}

        <div className={styles.steps}>
          {(['name', 'privacy', 'success'] as PlaylistStep[]).map((s, i) => (
            <div
              key={s}
              className={[
                styles.step,
                step === s ? styles.currentStep :
                ['name', 'privacy', 'success'].indexOf(step) > i ? styles.completeStep : '',
              ].filter(Boolean).join(' ')}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default QuickPlaylistModal;
