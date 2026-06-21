import formatDuration from 'format-duration';
import { useMemo, useState } from 'react';
import {
    MdKeyboardArrowDown,
    MdMusicNote,
    MdPause,
    MdPlayArrow,
    MdSkipNext,
    MdSkipPrevious,
    MdVolumeUp,
    MdRepeat,
    MdShuffle,
    MdQueueMusic,
    MdLyrics,
    MdFavorite,
    MdFavoriteBorder,
    MdBookmark,
    MdBookmarkBorder,
} from 'react-icons/md';
import { useNavigate } from 'react-router';

import styles from './consumer-screens.module.css';

import { useItemImageUrl } from '/@/renderer/components/item-image/item-image';
import { usePlayer } from '/@/renderer/features/player/context/player-context';
import { AppRoute } from '/@/renderer/router/routes';
import {
    usePlayerSong,
    usePlayerStatus,
    usePlayerTimestamp,
    usePlayerVolume,
    usePlayerQueue,
} from '/@/renderer/store';
import { LibraryItem } from '/@/shared/types/domain-types';
import { PlayerStatus } from '/@/shared/types/types';

type RepeatMode = 'off' | 'all' | 'one';

export default function NowPlayingScreen() {
    const navigate = useNavigate();
    const player = usePlayer();
    const currentSong = usePlayerSong();
    const status = usePlayerStatus();
    const timestamp = usePlayerTimestamp();
    const volume = usePlayerVolume();
    const queue = usePlayerQueue();
    
    const [repeatMode, setRepeatMode] = useState<RepeatMode>('off');
    const [shuffleMode, setShuffleMode] = useState(false);
    const [showQueue, setShowQueue] = useState(false);
    const [showLyrics, setShowLyrics] = useState(false);
    const [isLiked, setIsLiked] = useState(false);
    const [isSaved, setIsSaved] = useState(false);

    const coverUrl = useItemImageUrl({
        id: currentSong?.imageId,
        itemType: LibraryItem.SONG,
        serverId: currentSong?._serverId,
        type: 'itemCard',
    });

    const duration = currentSong?.duration ? currentSong.duration / 1000 : 0;
    const currentTime = Math.min(duration, timestamp);
    const totalLabel = useMemo(() => formatDuration(duration * 1000), [duration]);
    const elapsedLabel = useMemo(() => formatDuration(currentTime * 1000), [currentTime]);

    const handleRepeatToggle = () => {
        const modes: RepeatMode[] = ['off', 'all', 'one'];
        const currentIndex = modes.indexOf(repeatMode);
        const nextMode = modes[(currentIndex + 1) % modes.length];
        setRepeatMode(nextMode);
        // TODO: Call player.setRepeatMode(nextMode)
    };

    const handleShuffleToggle = () => {
        setShuffleMode(!shuffleMode);
        // TODO: Call player.setShuffleMode(!shuffleMode)
    };

    const handleLikeToggle = () => {
        setIsLiked(!isLiked);
        // TODO: Call API to like/unlike song
    };

    const handleSaveToggle = () => {
        setIsSaved(!isSaved);
        // TODO: Call API to save/unsave song
    };

    return (
        <div className={styles.playerScreen}>
            <div className={styles.playerTopBar}>
                <button
                    aria-label="Close now playing"
                    className={styles.playerTopButton}
                    onClick={() => {
                        if (window.history.length > 1) {
                            navigate(-1);
                            return;
                        }

                        navigate(AppRoute.HOME);
                    }}
                    type="button"
                >
                    <MdKeyboardArrowDown aria-hidden />
                </button>
                <div className={styles.playerTopCopy}>
                    <div className={styles.eyebrow}>Now playing</div>
                    <div className={styles.playerTopTitle}>Playing from your library</div>
                </div>
                <button
                    aria-label="Queue"
                    className={styles.playerTopButton}
                    onClick={() => setShowQueue(!showQueue)}
                    type="button"
                >
                    <MdQueueMusic aria-hidden />
                </button>
            </div>

            <div className={styles.playerHero}>
                <div className={styles.playerArt}>
                    {coverUrl ? (
                        <img alt={currentSong?.name || 'Album art'} src={coverUrl} />
                    ) : (
                        <MdMusicNote aria-hidden />
                    )}
                </div>
                <div className={styles.playerCopy}>
                    <h1>{currentSong?.name || 'Choose something to play'}</h1>
                    <p>
                        {currentSong?.artistName ||
                            currentSong?.albumArtistName ||
                            'Your next favorite track is waiting.'}
                    </p>
                </div>
            </div>

            <div className={styles.playerPanel}>
                <div className={styles.actionRow}>
                    <button
                        aria-label={isLiked ? 'Unlike' : 'Like'}
                        onClick={handleLikeToggle}
                        style={{ background: 'none', border: 'none', color: isLiked ? '#1db954' : 'rgba(255,255,255,0.7)', cursor: 'pointer' }}
                        type="button"
                    >
                        {isLiked ? <MdFavorite aria-hidden /> : <MdFavoriteBorder aria-hidden />}
                    </button>
                    <button
                        aria-label={isSaved ? 'Unsave' : 'Save'}
                        onClick={handleSaveToggle}
                        style={{ background: 'none', border: 'none', color: isSaved ? '#1db954' : 'rgba(255,255,255,0.7)', cursor: 'pointer' }}
                        type="button"
                    >
                        {isSaved ? <MdBookmark aria-hidden /> : <MdBookmarkBorder aria-hidden />}
                    </button>
                    <button
                        aria-label="Lyrics"
                        onClick={() => setShowLyrics(!showLyrics)}
                        style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.7)', cursor: 'pointer' }}
                        type="button"
                    >
                        <MdLyrics aria-hidden />
                    </button>
                </div>

                <div className={styles.progressRow}>
                    <span>{elapsedLabel}</span>
                    <input
                        aria-label="Playback progress"
                        max={duration || 0}
                        min={0}
                        onChange={(event) =>
                            player.mediaSeekToTimestamp(Number(event.currentTarget.value))
                        }
                        type="range"
                        value={currentTime}
                    />
                    <span>{totalLabel}</span>
                </div>

                <div className={styles.transportRow}>
                    <button
                        aria-label="Shuffle"
                        onClick={handleShuffleToggle}
                        style={{ background: 'none', border: 'none', color: shuffleMode ? '#1db954' : 'rgba(255,255,255,0.7)', cursor: 'pointer' }}
                        type="button"
                    >
                        <MdShuffle aria-hidden />
                    </button>
                    <button
                        aria-label="Previous"
                        onClick={() => player.mediaPrevious()}
                        type="button"
                    >
                        <MdSkipPrevious aria-hidden />
                    </button>
                    <button
                        aria-label={status === PlayerStatus.PLAYING ? 'Pause' : 'Play'}
                        className={styles.transportPrimary}
                        onClick={() => player.mediaTogglePlayPause()}
                        type="button"
                    >
                        {status === PlayerStatus.PLAYING ? (
                            <MdPause aria-hidden />
                        ) : (
                            <MdPlayArrow aria-hidden />
                        )}
                    </button>
                    <button aria-label="Next" onClick={() => player.mediaNext()} type="button">
                        <MdSkipNext aria-hidden />
                    </button>
                    <button
                        aria-label={`Repeat ${repeatMode}`}
                        onClick={handleRepeatToggle}
                        style={{ background: 'none', border: 'none', color: repeatMode !== 'off' ? '#1db954' : 'rgba(255,255,255,0.7)', cursor: 'pointer' }}
                        type="button"
                    >
                        <MdRepeat aria-hidden />
                        {repeatMode === 'one' && <span style={{ fontSize: '10px', position: 'absolute', bottom: '2px', right: '2px' }}>1</span>}
                    </button>
                </div>

                <div className={styles.volumeRow}>
                    <span>
                        <MdVolumeUp aria-hidden />
                    </span>
                    <input
                        aria-label="Volume"
                        max={100}
                        min={0}
                        onChange={(event) => player.setVolume(Number(event.currentTarget.value))}
                        type="range"
                        value={volume}
                    />
                </div>
            </div>

            {showLyrics && (
                <div className={styles.lyricsPanel}>
                    <div className={styles.lyricsHeader}>
                        <h3>Lyrics</h3>
                        <button
                            onClick={() => setShowLyrics(false)}
                            style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.7)', cursor: 'pointer', fontSize: '20px' }}
                            type="button"
                        >
                            ×
                        </button>
                    </div>
                    <div className={styles.lyricsContent}>
                        <p style={{ color: 'rgba(255,255,255,0.5)', textAlign: 'center', padding: '40px' }}>
                            Lyrics feature coming soon
                        </p>
                    </div>
                </div>
            )}

            {showQueue && (
                <div className={styles.queuePanel}>
                    <div className={styles.queueHeader}>
                        <h3>Queue</h3>
                        <button
                            onClick={() => setShowQueue(false)}
                            style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.7)', cursor: 'pointer', fontSize: '20px' }}
                            type="button"
                        >
                            ×
                        </button>
                    </div>
                    <div className={styles.queueContent}>
                        {queue && queue.length > 0 ? (
                            queue.map((song, index) => (
                                <div key={song.id} className={styles.queueItem}>
                                    <span>{index + 1}</span>
                                    <div>
                                        <div>{song.name}</div>
                                        <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>
                                            {song.artistName}
                                        </div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <p style={{ color: 'rgba(255,255,255,0.5)', textAlign: 'center', padding: '40px' }}>
                                Queue is empty
                            </p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
