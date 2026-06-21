import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router';

import styles from './consumer-screens.module.css';

import { MediaCard } from '/@/renderer/features/consumer/components';
import { genresQueries } from '/@/renderer/features/genres/api/genres-api';
import { usePlayer } from '/@/renderer/features/player/context/player-context';
import { searchQueries } from '/@/renderer/features/search/api/search-api';
import { useDebounce } from '/@/renderer/hooks/use-debounce';
import { useSearchHistory } from '/@/renderer/hooks/use-search-history';
import { AppRoute } from '/@/renderer/router/routes';
import { useCurrentServerId } from '/@/renderer/store';
import { GenreListSort, LibraryItem, SortOrder } from '/@/shared/types/domain-types';
import { Play } from '/@/shared/types/types';

const genreColors = ['#e13300', '#5038a0', '#148a08', '#bc5900', '#7d4b32', '#2d46b9'];

export default function SearchScreen() {
    const navigate = useNavigate();
    const player = usePlayer();
    const serverId = useCurrentServerId();
    const [query, setQuery] = useState('');
    const debouncedQuery = useDebounce(query, 300);
    const { history, addToHistory, clearHistory, removeFromHistory } = useSearchHistory();

    const genres = useQuery(
        genresQueries.list({
            options: {
                enabled: Boolean(serverId),
            },
            query: {
                limit: 12,
                sortBy: GenreListSort.NAME,
                sortOrder: SortOrder.ASC,
                startIndex: 0,
            },
            serverId,
        }),
    );

    const search = useQuery(
        searchQueries.search({
            options: {
                enabled: Boolean(serverId) && debouncedQuery.trim().length > 0,
            },
            query: {
                albumArtistLimit: 6,
                albumLimit: 6,
                query: debouncedQuery.trim(),
                songLimit: 8,
            },
            serverId,
        }),
    );

    const genreCards = useMemo(
        () =>
            (genres.data?.items ?? []).map((genre, index) => ({
                color: genreColors[index % genreColors.length],
                genre,
            })),
        [genres.data?.items],
    );

    const handleSearch = (searchQuery: string) => {
        setQuery(searchQuery);
        if (searchQuery.trim()) {
            addToHistory(searchQuery);
        }
    };

    const handleHistoryClick = (historyQuery: string) => {
        handleSearch(historyQuery);
    };

    const handleClearHistory = () => {
        clearHistory();
    };

    const isLoading = search.isLoading || genres.isLoading;

    return (
        <div className={styles.screen}>
            <div className={styles.topBar}>
                <h1>Search</h1>
                <input
                    className={styles.searchInput}
                    onChange={(event) => setQuery(event.currentTarget.value)}
                    placeholder="What do you want to hear?"
                    value={query}
                />
            </div>

            {debouncedQuery.trim() ? (
                <div className={styles.searchResults}>
                    {isLoading ? (
                        <SearchSkeleton />
                    ) : (
                        <>
                            <SearchSection
                                items={search.data?.songs ?? []}
                                onSelect={(songId) => {
                                    const song = search.data?.songs.find((item) => item.id === songId);
                                    if (!song) return;
                                    player.addToQueueByData([song], Play.NOW, song.id);
                                    navigate(AppRoute.NOW_PLAYING);
                                }}
                                title="Songs"
                                type={LibraryItem.SONG}
                            />
                            <SearchSection
                                items={search.data?.albums ?? []}
                                onSelect={(albumId) => {
                                    if (!serverId) return;
                                    player.addToQueueByFetch(
                                        serverId,
                                        [albumId],
                                        LibraryItem.ALBUM,
                                        Play.NOW,
                                    );
                                    navigate(AppRoute.NOW_PLAYING);
                                }}
                                title="Albums"
                                type={LibraryItem.ALBUM}
                            />
                            <SearchSection
                                items={search.data?.albumArtists ?? []}
                                onSelect={(artistId) => {
                                    if (!serverId) return;
                                    player.addToQueueByFetch(
                                        serverId,
                                        [artistId],
                                        LibraryItem.ALBUM_ARTIST,
                                        Play.NOW,
                                    );
                                    navigate(AppRoute.NOW_PLAYING);
                                }}
                                title="Artists"
                                type={LibraryItem.ALBUM_ARTIST}
                            />
                            {!search.data?.songs?.length && 
                             !search.data?.albums?.length && 
                             !search.data?.albumArtists?.length && (
                                <div className={styles.section}>
                                    <div className={styles.sectionHeader}>
                                        <h2>No results</h2>
                                    </div>
                                    <p style={{ color: 'rgba(255,255,255,0.6)' }}>
                                        No songs, albums, or artists found for "{debouncedQuery}"
                                    </p>
                                </div>
                            )}
                        </>
                    )}
                </div>
            ) : (
                <>
                    {history.length > 0 && (
                        <section className={styles.section}>
                            <div className={styles.sectionHeader}>
                                <h2>Recent searches</h2>
                                <button
                                    onClick={handleClearHistory}
                                    style={{
                                        background: 'none',
                                        border: 'none',
                                        color: 'rgba(255,255,255,0.6)',
                                        cursor: 'pointer',
                                        fontSize: '14px',
                                    }}
                                    type="button"
                                >
                                    Clear all
                                </button>
                            </div>
                            <div className={styles.horizontalRail}>
                                {history.map((item) => (
                                    <button
                                        className={styles.cardButton}
                                        key={item.timestamp}
                                        onClick={() => handleHistoryClick(item.query)}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'space-between',
                                            padding: '12px 16px',
                                        }}
                                        type="button"
                                    >
                                        <span>{item.query}</span>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                removeFromHistory(item.query);
                                            }}
                                            style={{
                                                background: 'none',
                                                border: 'none',
                                                color: 'rgba(255,255,255,0.4)',
                                                cursor: 'pointer',
                                                padding: '4px',
                                            }}
                                            type="button"
                                        >
                                            ×
                                        </button>
                                    </button>
                                ))}
                            </div>
                        </section>
                    )}
                    <section className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <h2>Browse all</h2>
                        </div>
                        <div className={styles.genreGrid}>
                            {genreCards.map(({ color, genre }) => (
                                <button
                                    className={styles.genreCard}
                                    key={genre.id}
                                    onClick={() => handleSearch(genre.name)}
                                    style={{ background: `linear-gradient(135deg, ${color}, #181818)` }}
                                    type="button"
                                >
                                    <span>{genre.name}</span>
                                </button>
                            ))}
                        </div>
                    </section>
                </>
            )}
        </div>
    );
}

function SearchSkeleton() {
    return (
        <>
            <section className={styles.section}>
                <div className={styles.sectionHeader}>
                    <h2>Songs</h2>
                </div>
                <div className={styles.searchGrid}>
                    {Array.from({ length: 8 }).map((_, index) => (
                        <div
                            className={styles.cardButton}
                            key={index}
                            style={{
                                background: 'rgba(255,255,255,0.05)',
                                minHeight: '80px',
                                borderRadius: '8px',
                            }}
                        />
                    ))}
                </div>
            </section>
            <section className={styles.section}>
                <div className={styles.sectionHeader}>
                    <h2>Albums</h2>
                </div>
                <div className={styles.searchGrid}>
                    {Array.from({ length: 6 }).map((_, index) => (
                        <div
                            className={styles.cardButton}
                            key={index}
                            style={{
                                background: 'rgba(255,255,255,0.05)',
                                minHeight: '80px',
                                borderRadius: '8px',
                            }}
                        />
                    ))}
                </div>
            </section>
            <section className={styles.section}>
                <div className={styles.sectionHeader}>
                    <h2>Artists</h2>
                </div>
                <div className={styles.searchGrid}>
                    {Array.from({ length: 6 }).map((_, index) => (
                        <div
                            className={styles.cardButton}
                            key={index}
                            style={{
                                background: 'rgba(255,255,255,0.05)',
                                minHeight: '80px',
                                borderRadius: '8px',
                            }}
                        />
                    ))}
                </div>
            </section>
        </>
    );
}

function SearchSection({
    items,
    onSelect,
    title,
    type,
}: {
    items: Array<{
        _serverId: string;
        albumArtistName?: string;
        artistName?: string;
        id: string;
        imageId: null | string;
        name: string;
    }>;
    onSelect: (id: string) => void;
    title: string;
    type: LibraryItem;
}) {
    if (!items.length) return null;

    return (
        <section className={styles.section}>
            <div className={styles.sectionHeader}>
                <h2>{title}</h2>
            </div>
            <div className={styles.searchGrid}>
                {items.map((item) => (
                    <button
                        className={styles.cardButton}
                        key={item.id}
                        onClick={() => onSelect(item.id)}
                        type="button"
                    >
                        <MediaCard
                            artist={item.artistName || item.albumArtistName || 'Unknown artist'}
                            imageId={item.imageId}
                            serverId={item._serverId}
                            title={item.name}
                            type={type}
                        />
                    </button>
                ))}
            </div>
        </section>
    );
}
