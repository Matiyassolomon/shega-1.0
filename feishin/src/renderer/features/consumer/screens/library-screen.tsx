import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router';

import styles from './consumer-screens.module.css';

import { albumQueries } from '/@/renderer/features/albums/api/album-api';
import { artistsQueries } from '/@/renderer/features/artists/api/artists-api';
import { LibraryListItem } from '/@/renderer/features/consumer/components';
import { usePlayer } from '/@/renderer/features/player/context/player-context';
import { playlistsQueries } from '/@/renderer/features/playlists/api/playlists-api';
import { useBackendAuth } from '/@/renderer/hooks/use-backend-auth';
import { useLikedSongs, useRecentlyPlayed, useMarketplacePlaylists } from '/@/renderer/api/hooks';
import { AppRoute } from '/@/renderer/router/routes';
import { useCurrentServerId } from '/@/renderer/store';
import {
    AlbumArtistListSort,
    AlbumListSort,
    LibraryItem,
    PlaylistListSort,
    SortOrder,
} from '/@/shared/types/domain-types';
import { Play } from '/@/shared/types/types';

type LibraryTab = 'liked' | 'downloaded' | 'recent' | 'playlists' | 'artists' | 'albums';

const tabs: LibraryTab[] = ['liked', 'downloaded', 'recent', 'playlists', 'artists', 'albums'];

export default function LibraryScreen() {
    const navigate = useNavigate();
    const player = usePlayer();
    const serverId = useCurrentServerId();
    const { isAuthenticated } = useBackendAuth();
    const [tab, setTab] = useState<LibraryTab>('playlists');

    // Backend hooks
    const likedSongs = useLikedSongs(50);
    const recentlyPlayed = useRecentlyPlayed(24, 50);
    const marketplacePlaylists = useMarketplacePlaylists();

    // Navidrome hooks
    const playlists = useQuery(
        playlistsQueries.list({
            options: {
                enabled: Boolean(serverId),
            },
            query: {
                limit: 20,
                sortBy: PlaylistListSort.UPDATED_AT,
                sortOrder: SortOrder.DESC,
                startIndex: 0,
            },
            serverId,
        }),
    );

    const artists = useQuery(
        artistsQueries.albumArtistList({
            options: {
                enabled: Boolean(serverId),
            },
            query: {
                limit: 20,
                sortBy: AlbumArtistListSort.PLAY_COUNT,
                sortOrder: SortOrder.DESC,
                startIndex: 0,
            },
            serverId,
        }),
    );

    const albums = useQuery(
        albumQueries.list({
            options: {
                enabled: Boolean(serverId),
            },
            query: {
                limit: 20,
                sortBy: AlbumListSort.RECENTLY_ADDED,
                sortOrder: SortOrder.DESC,
                startIndex: 0,
            },
            serverId,
        }),
    );

    const renderedItems = useMemo(() => {
        if (tab === 'liked') {
            if (!isAuthenticated) {
                return <div style={{ padding: '20px', color: 'rgba(255,255,255,0.6)' }}>Sign in to see your liked songs</div>;
            }
            if (likedSongs.isLoading) {
                return <div style={{ padding: '20px', color: 'rgba(255,255,255,0.6)' }}>Loading liked songs...</div>;
            }
            if (!likedSongs.data || likedSongs.data.length === 0) {
                return <div style={{ padding: '20px', color: 'rgba(255,255,255,0.6)' }}>No liked songs yet. Like songs to build your collection.</div>;
            }
            return likedSongs.data.map((item) => (
                <button
                    className={styles.listButton}
                    key={item.song_id}
                    onClick={() => {
                        // TODO: Play the song
                    }}
                    type="button"
                >
                    <LibraryListItem
                        caption={item.artist}
                        imageId={item.cover_art}
                        meta={`${item.play_count} plays`}
                        serverId=""
                        title={item.title}
                        type={LibraryItem.SONG}
                    />
                </button>
            ));
        }

        if (tab === 'downloaded') {
            return <div style={{ padding: '20px', color: 'rgba(255,255,255,0.6)' }}>Downloaded songs will appear here (offline feature coming soon)</div>;
        }

        if (tab === 'recent') {
            if (!isAuthenticated) {
                return <div style={{ padding: '20px', color: 'rgba(255,255,255,0.6)' }}>Sign in to see your recently played</div>;
            }
            if (recentlyPlayed.isLoading) {
                return <div style={{ padding: '20px', color: 'rgba(255,255,255,0.6)' }}>Loading recently played...</div>;
            }
            if (!recentlyPlayed.data || recentlyPlayed.data.length === 0) {
                return <div style={{ padding: '20px', color: 'rgba(255,255,255,0.6)' }}>No recently played songs. Start listening to build your history.</div>;
            }
            return recentlyPlayed.data.map((item) => (
                <button
                    className={styles.listButton}
                    key={item.song_id}
                    onClick={() => {
                        // TODO: Play the song
                    }}
                    type="button"
                >
                    <LibraryListItem
                        caption={item.artist}
                        imageId={item.cover_art}
                        meta={`${item.play_count} plays`}
                        serverId=""
                        title={item.title}
                        type={LibraryItem.SONG}
                    />
                </button>
            ));
        }

        if (tab === 'playlists') {
            const allPlaylists = [
                ...(playlists.data?.items ?? []).map((item) => ({
                    ...item,
                    source: 'navidrome' as const,
                })),
                ...(marketplacePlaylists.data ?? []).map((item) => ({
                    ...item,
                    source: 'marketplace' as const,
                })),
            ];

            return allPlaylists.map((item) => (
                <button
                    className={styles.listButton}
                    key={item.id || item.playlist_id}
                    onClick={() => {
                        if (item.source === 'navidrome' && serverId) {
                            player.addToQueueByFetch(
                                serverId,
                                [item.id],
                                LibraryItem.PLAYLIST,
                                Play.NOW,
                            );
                            navigate(AppRoute.NOW_PLAYING);
                        } else if (item.source === 'marketplace') {
                            navigate(AppRoute.MARKETPLACE);
                        }
                    }}
                    type="button"
                >
                    <LibraryListItem
                        caption={item.source === 'navidrome' ? `${item.songCount ?? 0} songs` : `${item.sales_count} sold`}
                        imageId={item.imageId || item.cover_art_path}
                        meta={item.source === 'navidrome' ? (item.owner || 'Playlist') : item.creator_name}
                        serverId={item._serverId || ''}
                        title={item.name || item.title}
                        type={LibraryItem.PLAYLIST}
                    />
                </button>
            ));
        }

        if (tab === 'artists') {
            return (artists.data?.items ?? []).map((item) => (
                <button
                    className={styles.listButton}
                    key={item.id}
                    onClick={() => {
                        if (!serverId) return;
                        player.addToQueueByFetch(
                            serverId,
                            [item.id],
                            LibraryItem.ALBUM_ARTIST,
                            Play.NOW,
                        );
                        navigate(AppRoute.NOW_PLAYING);
                    }}
                    type="button"
                >
                    <LibraryListItem
                        caption={`${item.albumCount ?? 0} releases`}
                        imageId={item.imageId}
                        meta="Artist"
                        serverId={item._serverId}
                        title={item.name}
                        type={LibraryItem.ALBUM_ARTIST}
                    />
                </button>
            ));
        }

        return (albums.data?.items ?? []).map((item) => (
            <button
                className={styles.listButton}
                key={item.id}
                onClick={() => {
                    if (!serverId) return;
                    player.addToQueueByFetch(serverId, [item.id], LibraryItem.ALBUM, Play.NOW);
                    navigate(AppRoute.NOW_PLAYING);
                }}
                type="button"
            >
                <LibraryListItem
                    caption={`${item.songCount ?? 0} songs`}
                    imageId={item.imageId}
                    meta={item.albumArtistName || 'Album'}
                    serverId={item._serverId}
                    title={item.name}
                    type={LibraryItem.ALBUM}
                />
            </button>
        ));
    }, [
        albums.data?.items,
        artists.data?.items,
        navigate,
        player,
        playlists.data?.items,
        marketplacePlaylists.data,
        serverId,
        tab,
        isAuthenticated,
        likedSongs.data,
        likedSongs.isLoading,
        recentlyPlayed.data,
        recentlyPlayed.isLoading,
    ]);

    return (
        <div className={styles.screen}>
            <div className={styles.topBar}>
                <h1>Your Library</h1>
            </div>

            <div className={styles.tabRow}>
                {tabs.map((tabName) => (
                    <button
                        className={tab === tabName ? styles.tabActive : styles.tab}
                        key={tabName}
                        onClick={() => setTab(tabName)}
                        type="button"
                    >
                        {tabName[0].toUpperCase() + tabName.slice(1)}
                    </button>
                ))}
            </div>

            <div className={styles.listStack}>{renderedItems}</div>
        </div>
    );
}
