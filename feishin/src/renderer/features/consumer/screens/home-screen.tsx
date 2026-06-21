import { useMemo } from 'react';
import { useNavigate } from 'react-router';

import styles from './consumer-screens.module.css';

import {
    useRecommendations,
    useTrending,
    useRecentlyPlayed,
} from '/@/renderer/api/hooks';
import { useBackendAuth } from '/@/renderer/hooks/use-backend-auth';
import { AppRoute } from '/@/renderer/router/routes';
import { toast } from '/@/shared/components/toast/toast';

type LookalikeUser = {
    similarity: number;
    user_id: number;
};

type RecentlyPlayedSong = {
    song_id: number;
    title: string;
    artist: string;
    album?: string | null;
    genre?: string | null;
    cover_art?: string | null;
    last_played: string | null;
    play_count: number;
};

const cardMetaStyle = {
    color: 'rgb(255 255 255 / 68%)',
    display: 'grid',
    gap: 4,
} as const;

export default function HomeScreen() {
    const navigate = useNavigate();
    const { isAuthenticated, userId } = useBackendAuth();
    
    const recommendations = useRecommendations('Ethiopia');
    const trending = useTrending('Ethiopia');
    const recentlyPlayed = useRecentlyPlayed(24, 10);

    const greeting = useMemo(() => {
        const hour = new Date().getHours();
        if (hour < 12) return 'Good morning';
        if (hour < 18) return 'Good afternoon';
        return 'Good evening';
    }, []);

    if (recommendations.error) {
        toast.error({
            message: 'Failed to load recommendations',
            title: 'Home',
        });
    }

    if (trending.error) {
        toast.error({
            message: 'Failed to load trending',
            title: 'Home',
        });
    }

    if (recentlyPlayed.error) {
        toast.error({
            message: 'Failed to load recently played',
            title: 'Home',
        });
    }

    const loading = recommendations.isLoading || trending.isLoading || recentlyPlayed.isLoading;
    const forYou = recommendations.data?.recommendations ?? [];
    const lookalikes = recommendations.data?.lookalike_audience ?? [];
    const trendingSongs = trending.data?.recommendations ?? [];
    const recentSongs = recentlyPlayed.data ?? [];

    return (
        <div className={styles.screen}>
            <div className={styles.hero}>
                <div>
                    <div className={styles.eyebrow}>For you</div>
                    <h1>{greeting}</h1>
                    <p>Your music, personalized from listening habits and live momentum.</p>
                </div>
                <button
                    className={styles.searchShortcut}
                    onClick={() => navigate(AppRoute.SEARCH)}
                    type="button"
                >
                    Search music
                </button>
            </div>

            {isAuthenticated && (
                <RecentlyPlayedSection items={recentSongs} loading={recentlyPlayed.isLoading} />
            )}
            <InsightRow lookalikes={lookalikes} loading={loading} />
            <SongSection
                items={forYou}
                loading={loading}
                onOpenMarketplace={() => navigate(AppRoute.MARKETPLACE)}
                title="Made For You"
            />
            <TrendingSection items={trendingSongs} loading={loading} title="Trending Right Now" />
        </div>
    );
}

function InsightRow({
    loading,
    lookalikes,
}: {
    loading: boolean;
    lookalikes: LookalikeUser[];
}) {
    return (
        <section className={styles.section}>
            <div className={styles.sectionHeader}>
                <h2>Taste Insights</h2>
            </div>
            <div className={styles.horizontalRail}>
                {loading && <div className={styles.cardButton}>Loading your profile...</div>}
                {!loading &&
                    lookalikes.map((item) => (
                        <div className={styles.cardButton} key={item.user_id}>
                            <div style={cardMetaStyle}>
                                <strong>Listener #{item.user_id}</strong>
                                <span>{Math.round(item.similarity * 100)}% taste match</span>
                            </div>
                        </div>
                    ))}
            </div>
        </section>
    );
}

function SongSection({
    items,
    loading,
    onOpenMarketplace,
    title,
}: {
    items: RecommendationSong[];
    loading: boolean;
    onOpenMarketplace: () => void;
    title: string;
}) {
    return (
        <section className={styles.section}>
            <div className={styles.sectionHeader}>
                <h2>{title}</h2>
            </div>
            <div className={styles.horizontalRail}>
                {loading && <div className={styles.cardButton}>Loading recommendations...</div>}
                {!loading &&
                    items.map((item) => (
                        <button
                            className={styles.cardButton}
                            key={item.song_id}
                            onClick={onOpenMarketplace}
                            type="button"
                        >
                            <div style={cardMetaStyle}>
                                <strong>{item.title}</strong>
                                <span>
                                    {item.artist} | {item.genre}
                                </span>
                                <span>
                                    Match {item.score.toFixed(1)}
                                    {item.qenet_mode ? ` | ${item.qenet_mode}` : ''}
                                </span>
                            </div>
                        </button>
                    ))}
            </div>
        </section>
    );
}

function TrendingSection({
    items,
    loading,
    title,
}: {
    items: TrendingSong[];
    loading: boolean;
    title: string;
}) {
    return (
        <section className={styles.section}>
            <div className={styles.sectionHeader}>
                <h2>{title}</h2>
            </div>
            <div className={styles.horizontalRail}>
                {loading && <div className={styles.cardButton}>Loading trends...</div>}
                {!loading && items.length === 0 && (
                    <div className={styles.cardButton}>No trending songs available</div>
                )}
                {!loading &&
                    items.map((item) => (
                        <div className={styles.cardButton} key={item.song_id}>
                            <div style={cardMetaStyle}>
                                <strong>{item.title}</strong>
                                <span>
                                    {item.artist}
                                    {item.country ? ` | ${item.country}` : ''}
                                </span>
                                <span>
                                    Hot {item.hot_score.toFixed(1)} | Momentum{' '}
                                    {item.momentum_score.toFixed(1)}
                                </span>
                            </div>
                        </div>
                    ))}
            </div>
        </section>
    );
}

function RecentlyPlayedSection({
    items,
    loading,
}: {
    items: RecentlyPlayedSong[];
    loading: boolean;
}) {
    const formatTimeAgo = (dateString: string | null) => {
        if (!dateString) return 'Unknown';
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
        
        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        return `${Math.floor(seconds / 86400)}d ago`;
    };

    return (
        <section className={styles.section}>
            <div className={styles.sectionHeader}>
                <h2>Recently Played</h2>
            </div>
            <div className={styles.horizontalRail}>
                {loading && <div className={styles.cardButton}>Loading recently played...</div>}
                {!loading && items.length === 0 && (
                    <div className={styles.cardButton}>
                        <div style={cardMetaStyle}>
                            <strong>No recent plays</strong>
                            <span>Start listening to build your history</span>
                        </div>
                    </div>
                )}
                {!loading &&
                    items.map((item) => (
                        <div className={styles.cardButton} key={item.song_id}>
                            <div style={cardMetaStyle}>
                                <strong>{item.title}</strong>
                                <span>{item.artist}</span>
                                <span>
                                    {formatTimeAgo(item.last_played)} | {item.play_count} plays
                                </span>
                            </div>
                        </div>
                    ))}
            </div>
        </section>
    );
}
