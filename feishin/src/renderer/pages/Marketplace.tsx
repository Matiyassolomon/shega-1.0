import { useState } from 'react';
import { useNavigate } from 'react-router';

import {
    useMarketplacePlaylists,
    useMarketplaceSongs,
    usePurchasePlaylist,
    usePurchaseSong,
    useSavePlaylist,
    useSecurePlaylistAccess,
    useSecureSongAccess,
} from '/@/renderer/api/hooks';
import PaymentModal from '/@/renderer/components/PaymentModal';
import { AppRoute } from '/@/renderer/router/routes';
import { Button } from '/@/shared/components/button/button';
import { Group } from '/@/shared/components/group/group';
import { Stack } from '/@/shared/components/stack/stack';
import { Text } from '/@/shared/components/text/text';
import { toast } from '/@/shared/components/toast/toast';

const MarketplacePage = () => {
    const navigate = useNavigate();
    const [donationModalOpen, setDonationModalOpen] = useState(false);
    const [selectedArtist, setSelectedArtist] = useState<string | null>(null);
    const [paymentModalOpen, setPaymentModalOpen] = useState(false);
    const [paymentItemType, setPaymentItemType] = useState<'song' | 'playlist'>('song');
    const [paymentItemId, setPaymentItemId] = useState<string>('');
    const [paymentItemTitle, setPaymentItemTitle] = useState<string>('');
    const [paymentItemPrice, setPaymentItemPrice] = useState<number>(0);
    
    const playlists = useMarketplacePlaylists();
    const songs = useMarketplaceSongs();
    
    const purchasePlaylistMutation = usePurchasePlaylist();
    const purchaseSongMutation = usePurchaseSong();
    const savePlaylistMutation = useSavePlaylist();
    const securePlaylistAccessMutation = useSecurePlaylistAccess();
    const secureSongAccessMutation = useSecureSongAccess();

    if (playlists.error) {
        toast.error({
            message: 'Failed to load playlists',
            title: 'Marketplace',
        });
    }

    if (songs.error) {
        toast.error({
            message: 'Failed to load songs',
            title: 'Marketplace',
        });
    }

    const handleBuy = async (playlistId: string) => {
        const playlist = playlists.data?.find(p => p.playlist_id === playlistId);
        if (playlist) {
            setPaymentItemType('playlist');
            setPaymentItemId(playlistId);
            setPaymentItemTitle(playlist.title);
            setPaymentItemPrice(playlist.price);
            setPaymentModalOpen(true);
        }
    };

    const handleBuySong = async (songId: string) => {
        const song = songs.data?.find(s => s.song_id === songId);
        if (song) {
            setPaymentItemType('song');
            setPaymentItemId(songId);
            setPaymentItemTitle(song.title);
            setPaymentItemPrice(song.price);
            setPaymentModalOpen(true);
        }
    };

    const handlePaymentComplete = async (_paymentId: string) => {
        try {
            if (paymentItemType === 'playlist') {
                await purchasePlaylistMutation.mutateAsync(paymentItemId);
            } else {
                await purchaseSongMutation.mutateAsync(paymentItemId);
            }
            toast.success({ message: 'Purchase completed successfully', title: 'Marketplace' });
        } catch (error: any) {
            toast.error({ message: error?.message || 'purchase failed', title: 'Marketplace' });
        }
    };

    const handleSave = async (playlistId: string) => {
        try {
            await savePlaylistMutation.mutateAsync(playlistId);
            toast.success({ message: 'Playlist saved to your profile', title: 'Marketplace' });
        } catch (error: any) {
            toast.error({ message: error?.message || 'save failed', title: 'Marketplace' });
        }
    };

    const handlePreview = async (playlistId: string) => {
        try {
            const result = await securePlaylistAccessMutation.mutateAsync(playlistId);
            if (!result.authorized) {
                toast.warn({
                    message: 'Buy this playlist first to unlock secure streaming.',
                    title: 'Marketplace',
                });
                return;
            }
            toast.success({
                message: result.stream_path || result.x_accel_redirect || 'Secure stream unlocked',
                title: 'Marketplace',
            });
        } catch (error: any) {
            toast.error({ message: error?.message || 'preview failed', title: 'Marketplace' });
        }
    };

    const handleUnlockSong = async (songId: string) => {
        try {
            const result = await secureSongAccessMutation.mutateAsync(songId);
            if (!result.authorized) {
                toast.warn({
                    message: 'Buy this song or subscribe first to unlock playback.',
                    title: 'Marketplace',
                });
                return;
            }
            toast.success({
                message: result.stream_path || 'Song stream unlocked',
                title: 'Marketplace',
            });
        } catch (error: any) {
            toast.error({ message: error?.message || 'unlock failed', title: 'Marketplace' });
        }
    };

    const handleArtistClick = (artistName: string) => {
        navigate(`/artist/${encodeURIComponent(artistName)}`);
    };

    const handleDonate = (artistName: string) => {
        setSelectedArtist(artistName);
        setDonationModalOpen(true);
    };

    const loading = playlists.isLoading || songs.isLoading;

    return (
        <Stack gap="md" p="lg">
            <Text fw={700} size="xl">
                Marketplace
            </Text>
            {loading && (
                <Stack gap="md">
                    {[1, 2, 3].map((i) => (
                        <Stack
                            key={i}
                            p="md"
                            style={{
                                background: 'var(--theme-colors-surface)',
                                borderRadius: 12,
                                opacity: 0.5,
                            }}
                        >
                            <div style={{ height: '20px', width: '60%', background: 'rgba(255,255,255,0.1)', borderRadius: 4 }} />
                            <div style={{ height: '16px', width: '40%', background: 'rgba(255,255,255,0.1)', borderRadius: 4 }} />
                        </Stack>
                    ))}
                </Stack>
            )}
            {!loading && playlists.data?.length === 0 && songs.data?.length === 0 && (
                <Stack p="xl" style={{ textAlign: 'center' }}>
                    <Text variant="secondary">No items available in the marketplace yet</Text>
                    <Text variant="secondary" size="sm">Check back later for new releases</Text>
                </Stack>
            )}
            {!loading && (
                <>
                    {playlists.data && playlists.data.length > 0 && (
                        <>
                            <Text fw={600} size="lg">
                                Playlists
                            </Text>
                            {playlists.data.map((playlist) => (
                                <Stack
                                    className="telegram-panel"
                                    gap="xs"
                                    key={playlist.playlist_id}
                                    p="md"
                                    style={{
                                        background: 'var(--theme-colors-surface)',
                                        borderRadius: 12,
                                    }}
                                >
                                    <Text fw={600}>{playlist.title}</Text>
                                    <Text variant="secondary">Creator: {playlist.creator_name}</Text>
                                    <Text 
                                        variant="secondary" 
                                        style={{ cursor: 'pointer', textDecoration: 'underline' }}
                                        onClick={() => playlist.artist_name && handleArtistClick(playlist.artist_name)}
                                    >
                                        Artist: {playlist.artist_name || 'Independent creator'}
                                        {playlist.artist_verified ? ' ✓' : ''}
                                    </Text>
                                    <Text variant="secondary">
                                        Price: {playlist.currency} {playlist.price}
                                    </Text>
                                    <Text variant="secondary">
                                        Saves: {playlist.save_count} • Sales: {playlist.sales_count} • Score:{' '}
                                        {playlist.social_score.toFixed(1)}
                                    </Text>
                                    <Group>
                                        <Button
                                            onClick={() => handlePreview(playlist.playlist_id)}
                                            variant="default"
                                        >
                                            Preview
                                        </Button>
                                        <Button onClick={() => handleSave(playlist.playlist_id)} variant="default">
                                            Save
                                        </Button>
                                        {playlist.artist_name && (
                                            <Button 
                                                onClick={() => handleDonate(playlist.artist_name!)}
                                                variant="default"
                                            >
                                                Donate
                                            </Button>
                                        )}
                                        <Button
                                            className="telegram-primary-btn"
                                            onClick={() => handleBuy(playlist.playlist_id)}
                                        >
                                            Buy {playlist.currency} {playlist.price}
                                        </Button>
                                    </Group>
                                </Stack>
                            ))}
                        </>
                    )}
                    {songs.data && songs.data.length > 0 && (
                        <>
                            <Text fw={600} mt="md" size="lg">
                                Songs
                            </Text>
                            {songs.data.map((song) => (
                                <Stack
                                    className="telegram-panel"
                                    gap="xs"
                                    key={song.song_id}
                                    p="md"
                                    style={{
                                        background: 'var(--theme-colors-surface)',
                                        borderRadius: 12,
                                    }}
                                >
                                    <Text fw={600}>{song.title}</Text>
                                    <Text 
                                        variant="secondary"
                                        style={{ cursor: 'pointer', textDecoration: 'underline' }}
                                        onClick={() => handleArtistClick(song.artist)}
                                    >
                                        Artist: {song.artist}
                                    </Text>
                                    <Text variant="secondary">
                                        Genre: {song.genre}
                                        {song.is_premium ? ' • Premium' : ''}
                                    </Text>
                                    <Text variant="secondary">
                                        Price: {song.currency} {song.price}
                                    </Text>
                                    <Text variant="secondary">
                                        Plays: {song.play_count_7d} • Likes: {song.like_count_7d} • Sales:{' '}
                                        {song.sales_count}
                                    </Text>
                                    <Group>
                                        <Button onClick={() => handleUnlockSong(song.song_id)} variant="default">
                                            Unlock Stream
                                        </Button>
                                        <Button 
                                            onClick={() => handleDonate(song.artist)}
                                            variant="default"
                                        >
                                            Donate
                                        </Button>
                                        <Button
                                            className="telegram-primary-btn"
                                            onClick={() => handleBuySong(song.song_id)}
                                        >
                                            Buy {song.currency} {song.price}
                                        </Button>
                                    </Group>
                                </Stack>
                            ))}
                        </>
                    )}
                </>
            )}
            
            {donationModalOpen && selectedArtist && (
                <Stack
                    p="lg"
                    style={{
                        position: 'fixed',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        background: 'var(--theme-colors-surface)',
                        borderRadius: 12,
                        zIndex: 1000,
                        maxWidth: 400,
                        width: '90%',
                        border: '1px solid rgba(255,255,255,0.1)',
                    }}
                >
                    <Text fw={700} size="lg">Donate to {selectedArtist}</Text>
                    <Text variant="secondary">Support your favorite artist with a donation</Text>
                    <Text variant="secondary" size="sm">Donation feature coming soon</Text>
                    <Group>
                        <Button onClick={() => setDonationModalOpen(false)} variant="default">
                            Close
                        </Button>
                        <Button className="telegram-primary-btn" disabled>
                            Donate
                        </Button>
                    </Group>
                </Stack>
            )}
            
            <PaymentModal
                isOpen={paymentModalOpen}
                onClose={() => setPaymentModalOpen(false)}
                itemType={paymentItemType}
                itemId={paymentItemId}
                itemTitle={paymentItemTitle}
                itemPrice={paymentItemPrice}
                onPaymentComplete={handlePaymentComplete}
            />
        </Stack>
    );
};

export default MarketplacePage;
