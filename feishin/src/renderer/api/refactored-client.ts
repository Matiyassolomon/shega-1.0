/**
 * Refactored API Client for New Backend Architecture
 * 
 * This client works with the new payment and music domains
 * that were refactored for clean separation and enterprise security.
 */

import axios from 'axios';

// API Base URLs for different domains
const PAYMENT_API_URL = 
    ((import.meta as any).env?.PAYMENT_API_URL as string | undefined) ||
    ((import.meta as any).env?.VITE_PAYMENT_API_URL as string | undefined) ||
    'http://localhost:8001';

const MUSIC_API_URL = 
    ((import.meta as any).env?.MUSIC_API_URL as string | undefined) ||
    ((import.meta as any).env?.VITE_MUSIC_API_URL as string | undefined) ||
    'http://localhost:8002';

const LEGACY_API_URL = 
    ((import.meta as any).env?.BACKEND_API as string | undefined) ||
    ((import.meta as any).env?.VITE_BACKEND_API as string | undefined) ||
    'http://localhost:8000';

// Create clients for different domains
export const paymentClient = axios.create({
    baseURL: PAYMENT_API_URL,
    timeout: 15000,
});

export const musicClient = axios.create({
    baseURL: MUSIC_API_URL,
    timeout: 10000,
});

export const legacyClient = axios.create({
    baseURL: LEGACY_API_URL,
    timeout: 10000,
});

// Storage keys
export const BACKEND_USER_ID_STORAGE_KEY = 'backend-user-id';
export const BACKEND_ACCESS_TOKEN_STORAGE_KEY = 'backend-access-token';

// Auth utilities
export const getBackendUserId = () => localStorage.getItem(BACKEND_USER_ID_STORAGE_KEY) || '1';
export const getBackendAccessToken = () =>
    localStorage.getItem(BACKEND_ACCESS_TOKEN_STORAGE_KEY) || '';

export const setBackendUserId = (userId: number | string) => {
    localStorage.setItem(BACKEND_USER_ID_STORAGE_KEY, String(userId));
};

export const setBackendAccessToken = (token: string) => {
    localStorage.setItem(BACKEND_ACCESS_TOKEN_STORAGE_KEY, token);
};

// Add auth interceptors to all clients
const addAuthInterceptor = (client: any) => {
    client.interceptors.request.use((config: any) => {
        const token = getBackendAccessToken();
        if (token) {
            config.headers = config.headers ?? {};
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    });
};

addAuthInterceptor(paymentClient);
addAuthInterceptor(musicClient);
addAuthInterceptor(legacyClient);

// Types for new API responses
export interface PaymentIntent {
    id: number;
    app_name: string;
    object_type: string;
    object_id: string;
    amount: number;
    currency: string;
    status: string;
    customer_id: string;
    merchant_id?: string;
    description?: string;
    success_url?: string;
    cancel_url?: string;
    webhook_url?: string;
    provider_transaction_id?: string;
    created_at: string;
    updated_at: string;
}

export interface PaymentProcessResponse {
    status: string;
    payment_url?: string;
    qr_code?: string;
    ussd_code?: string;
    provider_reference?: string;
    next_action?: string;
}

export interface SongResponse {
    id: number;
    title: string;
    artist: string;
    album?: string;
    genre?: string;
    duration_seconds?: number;
    file_path: string;
    file_size_bytes: number;
    mime_type: string;
    is_active: boolean;
    is_explicit: boolean;
    is_public: boolean;
    uploader_id: string;
    owner_id: string;
    song_metadata: any;
    tags: string[];
    created_at: string;
    updated_at: string;
    last_played_at?: string;
}

export interface PlaylistResponse {
    id: number;
    name: string;
    description?: string;
    owner_id: string;
    is_public: boolean;
    is_collaborative: boolean;
    cover_image_url?: string;
    song_count: number;
    total_duration_seconds: number;
    external_id?: string;
    playlist_metadata: any;
    tags: string[];
    created_at: string;
    updated_at: string;
    last_accessed_at?: string;
}

export interface MarketplaceListingResponse {
    id: number;
    item_type: string;
    item_id: number;
    title: string;
    description?: string;
    price: number;
    currency: string;
    seller_id: string;
    is_featured: boolean;
    sales_count: number;
    total_revenue: number;
    listing_metadata: any;
    tags: string[];
    created_at: string;
    updated_at: string;
    expires_at?: string;
}

export interface PurchaseResponse {
    id: number;
    buyer_id: string;
    seller_id: string;
    item_type: string;
    item_id: number;
    payment_intent_id: number;
    price: number;
    currency: string;
    status: string;
    event_metadata: any;
    created_at: string;
    updated_at: string;
    refunded_at?: string;
}

export interface UserSubscriptionResponse {
    id: number;
    user_id: string;
    subscription_type: string;
    payment_intent_id: number;
    status: string;
    starts_at: string;
    expires_at?: string;
    features: string[];
    event_metadata: any;
    created_at: string;
    updated_at: string;
    cancelled_at?: string;
}

export interface ArtistResponse {
    id: number;
    name: string;
    bio?: string;
    image_url?: string;
    external_id?: string;
    website_url?: string;
    social_media: any;
    is_verified: boolean;
    is_active: boolean;
    owner_id: string;
    artist_metadata: any;
    tags: string[];
    created_at: string;
    updated_at: string;
}

// Payment Domain API Functions
export const createPaymentIntent = async (payload: {
    app_name: string;
    object_type: string;
    object_id: string;
    amount: number;
    currency?: string;
    customer_id: string;
    merchant_id?: string;
    description?: string;
    success_url?: string;
    cancel_url?: string;
    webhook_url?: string;
}) => {
    const { data } = await paymentClient.post('/api/v1/payments/intents', payload);
    return data as PaymentIntent;
};

export const processPayment = async (paymentIntentId: number, payload: {
    payment_provider?: string;
    return_url?: string;
    cancel_url?: string;
}) => {
    const { data } = await paymentClient.post(`/api/v1/payments/${paymentIntentId}/process`, payload);
    return data as PaymentProcessResponse;
};

export const verifyPayment = async (paymentIntentId: number, payload: {
    provider_response?: any;
    transaction_id?: string;
}) => {
    const { data } = await paymentClient.post(`/api/v1/payments/${paymentIntentId}/verify`, payload);
    return data as { status: string; verified: boolean };
};

export const getPaymentStatus = async (paymentIntentId: number) => {
    const { data } = await paymentClient.get(`/api/v1/payments/intents/${paymentIntentId}`);
    return data as PaymentIntent;
};

export const createRefund = async (payload: {
    payment_intent_id: number;
    amount?: number;
    reason?: string;
}) => {
    const { data } = await paymentClient.post('/api/v1/payments/refunds', payload);
    return data;
};

// Music Domain API Functions
export const getSongs = async (params?: {
    limit?: number;
    offset?: number;
    genre?: string;
    artist?: string;
    search?: string;
}) => {
    const { data } = await musicClient.get('/api/v1/music/songs', { params });
    return data as { items: SongResponse[]; total: number; page: number; page_size: number };
};

export const getSong = async (songId: number) => {
    const { data } = await musicClient.get(`/api/v1/music/songs/${songId}`);
    return data as SongResponse;
};

export const createSong = async (payload: {
    title: string;
    artist: string;
    album?: string;
    genre?: string;
    duration_seconds?: number;
    file_path: string;
    uploader_id: string;
    owner_id: string;
}) => {
    const { data } = await musicClient.post('/api/v1/music/songs', payload);
    return data as SongResponse;
};

export const updateSong = async (songId: number, payload: Partial<SongResponse>) => {
    const { data } = await musicClient.put(`/api/v1/music/songs/${songId}`, payload);
    return data as SongResponse;
};

export const deleteSong = async (songId: number) => {
    await musicClient.delete(`/api/v1/music/songs/${songId}`);
};

export const recordPlayback = async (songId: number, payload: {
    user_id: string;
    source?: string;
    source_id?: string;
    device_type?: string;
    ip_address?: string;
    user_agent?: string;
}) => {
    const { data } = await musicClient.post(`/api/v1/music/songs/${songId}/playback`, payload);
    return data;
};

export const addSongSocialSignal = async (songId: number, payload: {
    user_id: string;
    signal_type: string;
    signal_value?: number;
}) => {
    const { data } = await musicClient.post(`/api/v1/music/songs/${songId}/signals/${payload.signal_type}`, payload);
    return data;
};

// Playlist API Functions
export const getPlaylists = async (params?: {
    limit?: number;
    offset?: number;
    owner_id?: string;
    search?: string;
}) => {
    const { data } = await musicClient.get('/api/v1/music/playlists', { params });
    return data as { items: PlaylistResponse[]; total: number; page: number; page_size: number };
};

export const getPlaylist = async (playlistId: number) => {
    const { data } = await musicClient.get(`/api/v1/music/playlists/${playlistId}`);
    return data as PlaylistResponse;
};

export const createPlaylist = async (payload: {
    name: string;
    description?: string;
    owner_id: string;
    is_public?: boolean;
}) => {
    const { data } = await musicClient.post('/api/v1/music/playlists', payload);
    return data as PlaylistResponse;
};

export const updatePlaylist = async (playlistId: number, payload: Partial<PlaylistResponse>) => {
    const { data } = await musicClient.put(`/api/v1/music/playlists/${playlistId}`, payload);
    return data as PlaylistResponse;
};

export const deletePlaylist = async (playlistId: number) => {
    await musicClient.delete(`/api/v1/music/playlists/${playlistId}`);
};

export const addSongToPlaylist = async (playlistId: number, payload: {
    song_id: number;
    position?: number;
}) => {
    const { data } = await musicClient.post(`/api/v1/music/playlists/${playlistId}/songs`, payload);
    return data;
};

export const removeSongFromPlaylist = async (playlistId: number, songId: number) => {
    await musicClient.delete(`/api/v1/music/playlists/${playlistId}/songs/${songId}`);
};

// Marketplace API Functions
export const getMarketplaceListings = async (params?: {
    limit?: number;
    offset?: number;
    item_type?: string;
    seller_id?: string;
    search?: string;
}) => {
    const { data } = await musicClient.get('/api/v1/music/marketplace/listings', { params });
    return data as { items: MarketplaceListingResponse[]; total: number; page: number; page_size: number };
};

export const createMarketplaceListing = async (payload: {
    item_type: string;
    item_id: number;
    title: string;
    description?: string;
    price: number;
    currency?: string;
    seller_id: string;
}) => {
    const { data } = await musicClient.post('/api/v1/music/marketplace/listings', payload);
    return data as MarketplaceListingResponse;
};

export const getMarketplaceListing = async (listingId: number) => {
    const { data } = await musicClient.get(`/api/v1/music/marketplace/listings/${listingId}`);
    return data as MarketplaceListingResponse;
};

// Integration API Functions (Music + Payment)
export const purchaseSong = async (songId: number, paymentProvider?: string) => {
    const { data } = await musicClient.post(`/api/v1/integration/purchase/song/${songId}`, {
        payment_provider: paymentProvider || 'telebirr'
    });
    return data as {
        status: string;
        song: SongResponse;
        listing: MarketplaceListingResponse;
        payment_intent: PaymentIntent;
        next_action: string;
    };
};

export const purchasePlaylist = async (playlistId: number, paymentProvider?: string) => {
    const { data } = await musicClient.post(`/api/v1/integration/purchase/playlist/${playlistId}`, {
        payment_provider: paymentProvider || 'telebirr'
    });
    return data as {
        status: string;
        playlist: PlaylistResponse;
        listing: MarketplaceListingResponse;
        payment_intent: PaymentIntent;
        next_action: string;
    };
};

export const purchaseSubscription = async (subscriptionType: string, paymentProvider?: string) => {
    const { data } = await musicClient.post(`/api/v1/integration/purchase/subscription/${subscriptionType}`, {
        payment_provider: paymentProvider || 'telebirr'
    });
    return data as {
        status: string;
        subscription_type: string;
        price: number;
        payment_intent: PaymentIntent;
        next_action: string;
    };
};

export const completePurchase = async (paymentIntentId: number) => {
    const { data } = await musicClient.post(`/api/v1/integration/complete/${paymentIntentId}`);
    return data as {
        status: string;
        purchase_type: string;
        song?: SongResponse;
        playlist?: PlaylistResponse;
        subscription?: UserSubscriptionResponse;
        purchase?: PurchaseResponse;
    };
};

export const getUserPurchases = async (params?: {
    limit?: number;
    offset?: number;
}) => {
    const { data } = await musicClient.get('/api/v1/integration/purchases', { params });
    return data as {
        purchases: any[];
        total: number;
        page: number;
        page_size: number;
    };
};

export const getUserRevenue = async (params?: {
    start_date?: string;
    end_date?: string;
}) => {
    const { data } = await musicClient.get('/api/v1/integration/revenue', { params });
    return data as {
        total_revenue: number;
        total_sales: number;
        period: {
            start?: string;
            end?: string;
        };
    };
};

// Search API Functions
export const searchMusic = async (params: {
    query: string;
    type?: string;
    limit?: number;
    offset?: number;
}) => {
    const { data } = await musicClient.get('/api/v1/music/search', { params });
    return data as {
        songs: SongResponse[];
        playlists: PlaylistResponse[];
        artists: ArtistResponse[];
        releases: any[];
        total: number;
        query: string;
    };
};

// Subscription API Functions
export const getUserSubscription = async (userId: string) => {
    const { data } = await musicClient.get(`/api/v1/music/subscriptions/user/${userId}`);
    return data as UserSubscriptionResponse;
};

export const checkUserSubscription = async (userId: string) => {
    const { data } = await musicClient.get(`/api/v1/music/subscriptions/check/${userId}`);
    return data as { subscribed: boolean; subscription?: UserSubscriptionResponse };
};

// Health Check Functions
export const checkPaymentHealth = async () => {
    const { data } = await paymentClient.get('/health');
    return data as { status: string; service: string };
};

export const checkMusicHealth = async () => {
    const { data } = await musicClient.get('/health');
    return data as { status: string; service: string };
};

export const checkMusicReadiness = async () => {
    const { data } = await musicClient.get('/health/ready');
    return data as {
        status: string;
        service: string;
        database: string;
        configuration: any;
        feature_flags: any;
    };
};

// Utility Functions
export const getPaymentProviders = () => {
    return [
        { id: 'telebirr', name: 'Telebirr', description: 'Mobile money via USSD' },
        { id: 'chapa', name: 'Chapa', description: 'Payment aggregator' },
        { id: 'cbe_bank', name: 'CBE Bank', description: 'Bank transfers and digital banking' },
        { id: 'manual_bank', name: 'Manual Bank', description: 'Manual verification' }
    ];
};

export const getSubscriptionTypes = () => {
    return [
        { id: 'premium', name: 'Premium Monthly', price: 99, description: 'Unlimited premium tracks for one month' },
        { id: 'premium_yearly', name: 'Premium Yearly', price: 990, description: 'Unlimited premium tracks for one year' }
    ];
};

// Error handling utilities
export const handleApiError = (error: any) => {
    if (error.response) {
        const { status, data } = error.response;
        return {
            message: data?.message || `HTTP ${status} error`,
            status,
            details: data
        };
    } else if (error.request) {
        return {
            message: 'Network error - please check your connection',
            status: 0,
            details: null
        };
    } else {
        return {
            message: error.message || 'Unknown error occurred',
            status: -1,
            details: error
        };
    }
};

// Migration utilities for backward compatibility
export const migrateToNewAPI = async () => {
    // This function can help migrate from old API to new domain-based APIs
    console.log('Migrating to new refactored API architecture...');
    
    // Test connectivity to new services
    try {
        const [paymentHealth, musicHealth] = await Promise.all([
            checkPaymentHealth(),
            checkMusicHealth()
        ]);
        
        console.log('Payment API Health:', paymentHealth);
        console.log('Music API Health:', musicHealth);
        
        return {
            payment_api_available: paymentHealth.status === 'healthy',
            music_api_available: musicHealth.status === 'healthy',
            migration_complete: true
        };
    } catch (error) {
        console.error('Migration failed:', error);
        return {
            payment_api_available: false,
            music_api_available: false,
            migration_complete: false,
            error: handleApiError(error)
        };
    }
};
