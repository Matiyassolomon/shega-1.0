// @ts-nocheck
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import {
    getMarketplacePlaylists,
    getMarketplaceSongs,
    purchasePlaylist,
    purchaseSong,
    savePlaylist,
    handleApiError,
    getBackendUserId,
} from '/@/renderer/api/aligned-client';
import { Stack } from '/@/shared/components/stack/stack';
import { Text } from '/@/shared/components/text/text';
import { toast } from '/@/shared/components/toast/toast';
import { AppRoute } from '/@/renderer/router/routes';
import { 
    ResponsiveLayout, 
    ResponsiveGrid, 
    ResponsiveCard, 
    ResponsiveButton 
} from '/@/renderer/components/ResponsiveLayout';

const AlignedMarketplacePage = () => {
    const userId = getBackendUserId();
    const [playlists, setPlaylists] = useState<LegacyPlaylistMarketplace[]>([]);
    const [songs, setSongs] = useState<LegacySongMarketplace[]>([]);
    const [purchasedItems, setPurchasedItems] = useState<Set<string>>(new Set());
    const [savedPlaylists, setSavedPlaylists] = useState<Set<string>>(new Set());
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        loadMarketplaceData();
    }, []);

    const loadMarketplaceData = async () => {
        setLoading(true);
        try {
            const [playlistData, songData] = await Promise.all([
                getMarketplacePlaylists(),
                getMarketplaceSongs(),
            ]);
            
            setPlaylists(playlistData);
            setSongs(songData);
        } catch (error: any) {
            const apiError = handleApiError(error);
            toast.error({ 
                message: apiError.message || 'Failed to load marketplace', 
                title: 'Marketplace Error' 
            });
        } finally {
            setLoading(false);
        }
    };

    const handlePlaylistPurchase = async (playlistId: string) => {
        try {
            const result = await purchasePlaylist({
                buyer_id: Number(userId),
                playlist_id: playlistId,
            });

            if (result.purchased) {
                setPurchasedItems(prev => new Set([...prev, `playlist_${playlistId}`]));
                toast.success({
                    message: 'Playlist purchased successfully!',
                    title: 'Purchase Complete',
                });
                
                // Update sales count
                setPlaylists(prev => prev.map(p => 
                    p.playlist_id === playlistId 
                        ? { ...p, sales_count: result.sales_count }
                        : p
                ));
            }
        } catch (error: any) {
            const apiError = handleApiError(error);
            toast.error({ 
                message: apiError.message, 
                title: 'Purchase Failed' 
            });
        }
    };

    const handleSongPurchase = async (songId: string) => {
        try {
            const result = await purchaseSong({
                buyer_id: Number(userId),
                song_id: songId,
            });

            if (result.purchased) {
                setPurchasedItems(prev => new Set([...prev, `song_${songId}`]));
                toast.success({
                    message: 'Song purchased successfully!',
                    title: 'Purchase Complete',
                });
                
                // Update sales count
                setSongs(prev => prev.map(s => 
                    s.song_id === songId 
                        ? { ...s, sales_count: result.sales_count }
                        : s
                ));
            }
        } catch (error: any) {
            const apiError = handleApiError(error);
            toast.error({ 
                message: apiError.message, 
                title: 'Purchase Failed' 
            });
        }
    };

    const handleSavePlaylist = async (playlistId: string) => {
        try {
            const result = await savePlaylist({
                playlist_id: playlistId,
                user_id: Number(userId),
            });

            if (result.saved) {
                setSavedPlaylists(prev => new Set([...prev, playlistId]));
                toast.success({
                    message: 'Playlist saved to your library!',
                    title: 'Playlist Saved',
                });
            } else {
                setSavedPlaylists(prev => {
                    const newSet = new Set(prev);
                    newSet.delete(playlistId);
                    return newSet;
                });
                toast.success({
                    message: 'Playlist removed from your library',
                    title: 'Playlist Unsaved',
                });
            }
        } catch (error: any) {
            const apiError = handleApiError(error);
            toast.error({ 
                message: apiError.message, 
                title: 'Save Failed' 
            });
        }
    };

    const formatPrice = (amount: number) => {
        return new Intl.NumberFormat('et-ET', {
            style: 'currency',
            currency: 'ETB',
        }).format(amount);
    };

    const formatDuration = (seconds?: number) => {
        if (!seconds) return '';
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const isPurchased = (type: 'playlist' | 'song', id: string) => {
        return purchasedItems.has(`${type}_${id}`);
    };

    return (
        <Stack gap="lg" p="lg">
            <Text fw={700} size="xl">
                Music Marketplace
            </Text>

            {/* Featured Playlists */}
            {playlists.filter(p => p.is_featured).length > 0 && (
                <Stack gap="md">
                    <Text fw={600}>Featured Playlists</Text>
                    <Group className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {playlists.filter(p => p.is_featured).map((playlist) => {
                            const isPlaylistPurchased = isPurchased('playlist', playlist.playlist_id);
                            const isSaved = savedPlaylists.has(playlist.playlist_id);
                            
                            return (
                                <Stack key={playlist.id} className="telegram-panel" gap="sm" p="md">
                                    <Stack direction="row" justify="space-between" align="center">
                                        <Text fw={600} truncate>{playlist.title}</Text>
                                        {playlist.is_featured && (
                                            <Text size="xs" className="bg-yellow-500 text-white px-2 py-1 rounded">
                                                Featured
                                            </Text>
                                        )}
                                    </Stack>
                                    
                                    <Text size="sm" variant="secondary">
                                        by {playlist.creator_name}
                                    </Text>
                                    
                                    {playlist.artist_name && (
                                        <Text size="sm" variant="secondary">
                                            {playlist.artist_name}
                                            {playlist.artist_verified && ' ✓'}
                                        </Text>
                                    )}
                                    
                                    <Text size="sm" variant="secondary" truncate>
                                        {playlist.description}
                                    </Text>
                                    
                                    <Stack direction="row" justify="space-between" align="center">
                                        <Text fw={700} size="lg" className="text-green-500">
                                            {formatPrice(playlist.price)}
                                        </Text>
                                        <Text size="xs" variant="secondary">
                                            {playlist.sales_count} sales
                                        </Text>
                                    </Stack>
                                    
                                    <Stack direction="row" gap="sm">
                                        <Button
                                            className={`telegram-primary-btn flex-1 ${isPlaylistPurchased ? 'opacity-50' : ''}`}
                                            onClick={() => handlePlaylistPurchase(playlist.playlist_id)}
                                            disabled={isPlaylistPurchased}
                                        >
                                            {isPlaylistPurchased ? 'Purchased' : 'Buy'}
                                        </Button>
                                        
                                        <Button
                                            className={`telegram-secondary-btn ${isSaved ? 'opacity-50' : ''}`}
                                            onClick={() => handleSavePlaylist(playlist.playlist_id)}
                                        >
                                            {isSaved ? 'Saved' : 'Save'}
                                        </Button>
                                    </Stack>
                                </Stack>
                            );
                        })}
                    </Group>
                </Stack>
            )}

            {/* All Playlists */}
            {playlists.length > 0 && (
                <Stack gap="md">
                    <Text fw={600}>All Playlists</Text>
                    <Group className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {playlists.filter(p => !p.is_featured).map((playlist) => {
                            const isPlaylistPurchased = isPurchased('playlist', playlist.playlist_id);
                            const isSaved = savedPlaylists.has(playlist.playlist_id);
                            
                            return (
                                <Stack key={playlist.id} className="telegram-panel" gap="sm" p="md">
                                    <Text fw={600} truncate>{playlist.title}</Text>
                                    <Text size="sm" variant="secondary">
                                        by {playlist.creator_name}
                                    </Text>
                                    
                                    {playlist.artist_name && (
                                        <Text size="sm" variant="secondary">
                                            {playlist.artist_name}
                                            {playlist.artist_verified && ' ✓'}
                                        </Text>
                                    )}
                                    
                                    <Stack direction="row" justify="space-between" align="center">
                                        <Text fw={700} className="text-green-500">
                                            {formatPrice(playlist.price)}
                                        </Text>
                                        <Text size="xs" variant="secondary">
                                            {playlist.sales_count} sales
                                        </Text>
                                    </Stack>
                                    
                                    <Stack direction="row" gap="sm">
                                        <Button
                                            className={`telegram-primary-btn flex-1 ${isPlaylistPurchased ? 'opacity-50' : ''}`}
                                            onClick={() => handlePlaylistPurchase(playlist.playlist_id)}
                                            disabled={isPlaylistPurchased}
                                        >
                                            {isPlaylistPurchased ? 'Purchased' : 'Buy'}
                                        </Button>
                                        
                                        <Button
                                            className={`telegram-secondary-btn ${isSaved ? 'opacity-50' : ''}`}
                                            onClick={() => handleSavePlaylist(playlist.playlist_id)}
                                        >
                                            {isSaved ? 'Saved' : 'Save'}
                                        </Button>
                                    </Stack>
                                </Stack>
                            );
                        })}
                    </Group>
                </Stack>
            )}

            {/* Songs */}
            {songs.length > 0 && (
                <Stack gap="md">
                    <Text fw={600}>Individual Songs</Text>
                    <Group className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {songs.map((song) => {
                            const isSongPurchased = isPurchased('song', song.song_id);
                            
                            return (
                                <Stack key={song.id} className="telegram-panel" gap="sm" p="md">
                                    <Stack direction="row" justify="space-between" align="center">
                                        <Text fw={600} truncate>{song.title}</Text>
                                        {song.is_featured && (
                                            <Text size="xs" className="bg-yellow-500 text-white px-2 py-1 rounded">
                                                Featured
                                            </Text>
                                        )}
                                    </Stack>
                                    
                                    <Text size="sm" variant="secondary">
                                        {song.artist}
                                    </Text>
                                    
                                    {song.album && (
                                        <Text size="sm" variant="secondary">
                                            {song.album}
                                        </Text>
                                    )}
                                    
                                    {song.duration_seconds && (
                                        <Text size="sm" variant="secondary">
                                            {formatDuration(song.duration_seconds)}
                                        </Text>
                                    )}
                                    
                                    <Stack direction="row" justify="space-between" align="center">
                                        <Text fw={700} className="text-green-500">
                                            {formatPrice(song.price)}
                                        </Text>
                                        <Text size="xs" variant="secondary">
                                            {song.sales_count} sales
                                        </Text>
                                    </Stack>
                                    
                                    <Button
                                        className={`telegram-primary-btn ${isSongPurchased ? 'opacity-50' : ''}`}
                                        onClick={() => handleSongPurchase(song.song_id)}
                                        disabled={isSongPurchased}
                                    >
                                        {isSongPurchased ? 'Purchased' : 'Buy Song'}
                                    </Button>
                                </Stack>
                            );
                        })}
                    </Group>
                </Stack>
            )}

            {/* Empty State */}
            {!loading && playlists.length === 0 && songs.length === 0 && (
                <Stack className="telegram-panel" gap="md" p="lg" align="center">
                    <Text fw={600} size="lg">
                        No items in marketplace
                    </Text>
                    <Text variant="secondary">
                        Check back later for new songs and playlists
                    </Text>
                </Stack>
            )}

            {/* Loading State */}
            {loading && (
                <Stack className="telegram-panel" gap="md" p="lg" align="center">
                    <Text>Loading marketplace...</Text>
                </Stack>
            )}
        </Stack>
    );
};

export default AlignedMarketplacePage;
