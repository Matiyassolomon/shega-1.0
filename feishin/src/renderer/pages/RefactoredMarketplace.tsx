import { useEffect, useState } from 'react';
import {
    getMarketplaceListings,
    purchaseSong,
    purchasePlaylist,
    searchMusic,
    getUserPurchases,
    handleApiError,
    type MarketplaceListingResponse,
    type SongResponse,
    type PlaylistResponse,
    type PaymentIntent,
    getBackendUserId,
} from '/@/renderer/api/refactored-client';
import { Button } from '/@/shared/components/button/button';
import { Group } from '/@/shared/components/group/group';
import { Stack } from '/@/shared/components/stack/stack';
import { Text } from '/@/shared/components/text/text';
import { toast } from '/@/shared/components/toast/toast';

const RefactoredMarketplacePage = () => {
    const userId = getBackendUserId();
    const [listings, setListings] = useState<MarketplaceListingResponse[]>([]);
    const [songs, setSongs] = useState<SongResponse[]>([]);
    const [playlists, setPlaylists] = useState<PlaylistResponse[]>([]);
    const [purchases, setPurchases] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [paymentIntent, setPaymentIntent] = useState<PaymentIntent | null>(null);
    const [selectedProvider, setSelectedProvider] = useState('telebirr');

    useEffect(() => {
        let mounted = true;
        const loadMarketplaceData = async () => {
            setLoading(true);
            try {
                // Load marketplace listings
                const listingsData = await getMarketplaceListings({
                    limit: 50,
                    offset: 0,
                });
                
                if (mounted) {
                    setListings(listingsData.items);
                }

                // Load user purchases
                const purchasesData = await getUserPurchases({ limit: 100 });
                if (mounted) {
                    setPurchases(purchasesData.purchases || []);
                }
            } catch (error: any) {
                const apiError = handleApiError(error);
                toast.error({ 
                    message: apiError.message || 'Failed to load marketplace', 
                    title: 'Marketplace Error' 
                });
            } finally {
                if (mounted) setLoading(false);
            }
        };

        loadMarketplaceData();
        return () => {
            mounted = false;
        };
    }, []);

    const handleSearch = async () => {
        if (!searchQuery.trim()) return;

        setLoading(true);
        try {
            const searchResults = await searchMusic({
                query: searchQuery,
                type: selectedCategory === 'all' ? undefined : selectedCategory,
                limit: 20,
            });

            setSongs(searchResults.songs);
            setPlaylists(searchResults.playlists);
        } catch (error: any) {
            const apiError = handleApiError(error);
            toast.error({ 
                message: apiError.message, 
                title: 'Search Error' 
            });
        } finally {
            setLoading(false);
        }
    };

    const handleSongPurchase = async (songId: number) => {
        try {
            const purchaseResult = await purchaseSong(songId, selectedProvider);
            
            if (purchaseResult.status === 'payment_required') {
                setPaymentIntent(purchaseResult.payment_intent);
                
                // In a real app, this would redirect to payment provider
                toast.success({
                    message: `Payment intent created for ${purchaseResult.song.title}`,
                    title: 'Purchase Initiated',
                });
                
                // Simulate payment processing (in real app, redirect to provider)
                setTimeout(() => {
                    completePurchase(purchaseResult.payment_intent.id);
                }, 2000);
            }
        } catch (error: any) {
            const apiError = handleApiError(error);
            toast.error({ 
                message: apiError.message, 
                title: 'Purchase Failed' 
            });
        }
    };

    const handlePlaylistPurchase = async (playlistId: number) => {
        try {
            const purchaseResult = await purchasePlaylist(playlistId, selectedProvider);
            
            if (purchaseResult.status === 'payment_required') {
                setPaymentIntent(purchaseResult.payment_intent);
                
                toast.success({
                    message: `Payment intent created for ${purchaseResult.playlist.name}`,
                    title: 'Purchase Initiated',
                });
                
                // Simulate payment processing
                setTimeout(() => {
                    completePurchase(purchaseResult.payment_intent.id);
                }, 2000);
            }
        } catch (error: any) {
            const apiError = handleApiError(error);
            toast.error({ 
                message: apiError.message, 
                title: 'Purchase Failed' 
            });
        }
    };

    const completePurchase = async (paymentIntentId: number) => {
        try {
            // This would normally be called after payment provider callback
            const { completePurchase } = await import('/@/renderer/api/refactored-client');
            const result = await completePurchase(paymentIntentId);
            
            if (result.status === 'completed') {
                toast.success({
                    message: 'Purchase completed successfully!',
                    title: 'Payment Complete',
                });
                
                // Reload purchases
                const purchasesData = await getUserPurchases({ limit: 100 });
                setPurchases(purchasesData.purchases || []);
                
                setPaymentIntent(null);
            }
        } catch (error: any) {
            const apiError = handleApiError(error);
            toast.error({ 
                message: apiError.message, 
                title: 'Purchase Completion Failed' 
            });
        }
    };

    const formatPrice = (amount: number) => {
        return new Intl.NumberFormat('et-ET', {
            style: 'currency',
            currency: 'ETB',
        }).format(amount);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString();
    };

    const isPurchased = (itemType: string, itemId: number) => {
        return purchases.some(purchase => 
            purchase.item_type === itemType && purchase.item_id === itemId
        );
    };

    const getListingsByType = (type: string) => {
        return listings.filter(listing => listing.item_type === type);
    };

    const songListings = getListingsByType('song');
    const playlistListings = getListingsByType('playlist');

    return (
        <Stack gap="lg" p="lg">
            <Text fw={700} size="xl">
                Music Marketplace
            </Text>

            {/* Search and Filters */}
            <Stack className="telegram-panel" gap="md" p="md">
                <Text fw={600}>Search & Discover</Text>
                <Stack direction="row" gap="md" align="center">
                    <input
                        type="text"
                        placeholder="Search songs, playlists, artists..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    />
                    <Button
                        className="telegram-primary-btn"
                        onClick={handleSearch}
                        disabled={loading}
                    >
                        {loading ? 'Searching...' : 'Search'}
                    </Button>
                </Stack>
                
                <Stack direction="row" gap="sm">
                    {['all', 'song', 'playlist', 'artist'].map((category) => (
                        <Button
                            key={category}
                            className={`telegram-secondary-btn ${selectedCategory === category ? 'selected' : ''}`}
                            onClick={() => setSelectedCategory(category)}
                            variant={selectedCategory === category ? 'primary' : 'secondary'}
                            size="sm"
                        >
                            {category.charAt(0).toUpperCase() + category.slice(1)}
                        </Button>
                    ))}
                </Stack>
            </Stack>

            {/* Songs Section */}
            {songListings.length > 0 && (
                <Stack gap="md">
                    <Text fw={600}>Songs for Sale</Text>
                    <Group className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {songListings.map((listing) => {
                            const isSongPurchased = isPurchased('song', listing.item_id);
                            return (
                                <Stack key={listing.id} className="telegram-panel" gap="sm" p="md">
                                    <Text fw={600} truncate>{listing.title}</Text>
                                    <Text size="sm" variant="secondary">
                                        {listing.description}
                                    </Text>
                                    <Stack direction="row" justify="space-between" align="center">
                                        <Text fw={700} size="lg" className="text-green-500">
                                            {formatPrice(listing.price)}
                                        </Text>
                                        {listing.is_featured && (
                                            <Text size="xs" className="bg-yellow-500 text-white px-2 py-1 rounded">
                                                Featured
                                            </Text>
                                        )}
                                    </Stack>
                                    <Text size="xs" variant="secondary">
                                        {listing.sales_count} sales
                                    </Text>
                                    <Button
                                        className={`telegram-primary-btn ${isSongPurchased ? 'opacity-50' : ''}`}
                                        onClick={() => handleSongPurchase(listing.item_id)}
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

            {/* Playlists Section */}
            {playlistListings.length > 0 && (
                <Stack gap="md">
                    <Text fw={600}>Playlists for Sale</Text>
                    <Group className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {playlistListings.map((listing) => {
                            const isPlaylistPurchased = isPurchased('playlist', listing.item_id);
                            return (
                                <Stack key={listing.id} className="telegram-panel" gap="sm" p="md">
                                    <Text fw={600} truncate>{listing.title}</Text>
                                    <Text size="sm" variant="secondary">
                                        {listing.description}
                                    </Text>
                                    <Stack direction="row" justify="space-between" align="center">
                                        <Text fw={700} size="lg" className="text-green-500">
                                            {formatPrice(listing.price)}
                                        </Text>
                                        {listing.is_featured && (
                                            <Text size="xs" className="bg-yellow-500 text-white px-2 py-1 rounded">
                                                Featured
                                            </Text>
                                        )}
                                    </Stack>
                                    <Text size="xs" variant="secondary">
                                        {listing.sales_count} sales
                                    </Text>
                                    <Button
                                        className={`telegram-primary-btn ${isPlaylistPurchased ? 'opacity-50' : ''}`}
                                        onClick={() => handlePlaylistPurchase(listing.item_id)}
                                        disabled={isPlaylistPurchased}
                                    >
                                        {isPlaylistPurchased ? 'Purchased' : 'Buy Playlist'}
                                    </Button>
                                </Stack>
                            );
                        })}
                    </Group>
                </Stack>
            )}

            {/* Search Results */}
            {searchQuery && (songs.length > 0 || playlists.length > 0) && (
                <Stack gap="md">
                    <Text fw={600}>Search Results</Text>
                    
                    {songs.length > 0 && (
                        <Stack gap="sm">
                            <Text fw={600}>Songs</Text>
                            <Group className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {songs.map((song) => (
                                    <Stack key={song.id} className="telegram-panel" gap="sm" p="md">
                                        <Text fw={600} truncate>{song.title}</Text>
                                        <Text size="sm" variant="secondary">
                                            {song.artist}
                                        </Text>
                                        {song.album && (
                                            <Text size="sm" variant="secondary">
                                                {song.album}
                                            </Text>
                                        )}
                                        <Text size="sm" variant="secondary">
                                            {song.duration_seconds ? `${Math.floor(song.duration_seconds / 60)}:${(song.duration_seconds % 60).toString().padStart(2, '0')}` : ''}
                                        </Text>
                                    </Stack>
                                ))}
                            </Group>
                        </Stack>
                    )}
                    
                    {playlists.length > 0 && (
                        <Stack gap="sm">
                            <Text fw={600}>Playlists</Text>
                            <Group className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {playlists.map((playlist) => (
                                    <Stack key={playlist.id} className="telegram-panel" gap="sm" p="md">
                                        <Text fw={600} truncate>{playlist.name}</Text>
                                        <Text size="sm" variant="secondary">
                                            {playlist.description}
                                        </Text>
                                        <Text size="sm" variant="secondary">
                                            {playlist.song_count} songs
                                        </Text>
                                    </Stack>
                                ))}
                            </Group>
                        </Stack>
                    )}
                </Stack>
            )}

            {/* Payment Processing Modal */}
            {paymentIntent && (
                <Stack className="telegram-panel fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" gap="md" p="lg">
                    <Stack className="bg-white rounded-lg p-6 max-w-md w-full" gap="md">
                        <Text fw={600}>Processing Payment</Text>
                        <Text size="sm" variant="secondary">
                            Payment Intent ID: {paymentIntent.id}
                        </Text>
                        <Text size="sm" variant="secondary">
                            Amount: {formatPrice(paymentIntent.amount)}
                        </Text>
                        <Text size="sm" className="text-blue-500">
                            Processing payment with {selectedProvider}...
                        </Text>
                        <Button
                            className="telegram-primary-btn"
                            onClick={() => setPaymentIntent(null)}
                        >
                            Close
                        </Button>
                    </Stack>
                </Stack>
            )}

            {/* Empty State */}
            {!loading && listings.length === 0 && !searchQuery && (
                <Stack className="telegram-panel" gap="md" p="lg" align="center">
                    <Text fw={600} size="lg">
                        No items in marketplace
                    </Text>
                    <Text variant="secondary">
                        Check back later for new songs and playlists
                    </Text>
                </Stack>
            )}
        </Stack>
    );
};

export default RefactoredMarketplacePage;
