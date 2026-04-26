/**
 * Aligned API Client for Current Backend Implementation
 * 
 * This client matches the actual backend routes and schemas that exist
 * in the codebase, not the theoretical routes from the refactored design.
 */

import axios from 'axios';

// Backend API URL - use relative URL for Vite proxy
const BACKEND_API_URL = 
    ((import.meta as any).env?.BACKEND_API as string | undefined) ||
    ((import.meta as any).env?.VITE_BACKEND_API as string | undefined) ||
    ''; // Use relative URL for Vite proxy

// Create client
export const backendClient = axios.create({
    baseURL: BACKEND_API_URL,
    timeout: 15000,
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

// Add auth interceptor
backendClient.interceptors.request.use((config) => {
    const token = getBackendAccessToken();
    if (token) {
        config.headers = config.headers ?? {};
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Types for current backend API
export interface LegacyPayment {
    id: number;
    user_id: number;
    amount: number;
    method: string;
    payment_type: string;
    playlist_id?: string;
    status: string;
    created_at: string;
    redirect_url?: string; // Added to mirror expected H5 payment redirect flow
    payment_id?: number; // Added to mirror usage in Payments.tsx (e.g., result.payment_id || result.id)
}

export interface LegacyPlaylistMarketplace {
    id: number;
    playlist_id: string;
    seller_id: number;
    price: number;
    currency: string;
    is_featured: boolean;
    sales_count: number;
    title: string;
    description?: string;
    cover_art_path?: string;
    creator_name: string;
    artist_name?: string;
    artist_verified: boolean;
    preview_song_id?: string;
    region?: string;
}

export interface LegacySongMarketplace {
    id: number;
    song_id: string;
    seller_id: number;
    price: number;
    currency: string;
    is_featured: boolean;
    sales_count: number;
    title: string;
    artist: string;
    album?: string;
    duration_seconds?: number;
    file_path: string;
    cover_art_path?: string;
    preview_url?: string;
}

// Current Backend API Functions

// Payment API (Legacy Routes)
export const createPayment = async (payload: {
    amount: number;
    method: 'cbe' | 'telebirr';
    playlist_id?: string;
    song_id?: string;
    user_id: number | string;
    payment_type?: string;
}) => {
    const { data } = await backendClient.post('/payment/create', payload);
    return data as LegacyPayment;
};

export const confirmPayment = async (payload: {
    payment_id: number;
}) => {
    const { data } = await backendClient.post('/payment/confirm', payload);
    return data as {
        payment_id: number;
        status: string;
        subscription_status?: string;
        expires_at?: string;
    };
};

// Marketplace API (Legacy Routes)
export const getMarketplacePlaylists = async () => {
    const { data } = await backendClient.get('/marketplace');
    return data as LegacyPlaylistMarketplace[];
};

export const getMarketplaceSongs = async () => {
    const { data } = await backendClient.get('/marketplace/songs');
    return data as LegacySongMarketplace[];
};

export const purchasePlaylist = async (payload: {
    buyer_id: number;
    playlist_id: string;
}) => {
    const { data } = await backendClient.post('/marketplace/buy-playlist', payload);
    return data as {
        buyer_id: number;
        purchased: boolean;
        sales_count: number;
        playlist_id: string;
    };
};

export const purchaseSong = async (payload: {
    buyer_id: number;
    song_id: string;
}) => {
    const { data } = await backendClient.post('/marketplace/buy-song', payload);
    return data as {
        buyer_id: number;
        purchased: boolean;
        sales_count: number;
        song_id: string;
    };
};

export const savePlaylist = async (payload: {
    playlist_id: string;
    user_id: number;
}) => {
    const { data } = await backendClient.post('/marketplace/save-playlist', payload);
    return data as {
        playlist_id: string;
        save_count: number;
        saved: boolean;
    };
};

export const getSecurePlaylistAccess = async (playlistId: string, userId: number) => {
    const { data } = await backendClient.get(`/marketplace/secure-access/${playlistId}`, {
        params: { user_id: userId }
    });
    return data as {
        has_access: boolean;
        playlist: any;
        songs: any[];
    };
};

export const getSecureSongAccess = async (songId: string, userId: number) => {
    const { data } = await backendClient.get(`/marketplace/secure-song-access/${songId}`, {
        params: { user_id: userId }
    });
    return data as {
        has_access: boolean;
        song: any;
    };
};

// User API
export const getUserProfile = async (userId: string) => {
    const { data } = await backendClient.get(`/users/${userId}/profile`);
    return data as any;
};

export const checkSubscription = async (userId: string) => {
    const { data } = await backendClient.get('/subscription/check', {
        params: { user_id: userId }
    });
    return data as { subscribed: boolean };
};

// Recommendations API
export const getRecommendations = async (userId: string, location?: string) => {
    const { data } = await backendClient.get('/recommendations/playlists', {
        params: { location, user_id: userId }
    });
    return data as any;
};

export const getTrending = async (location?: string) => {
    const { data } = await backendClient.get('/recommendations/trending', {
        params: { location }
    });
    return data as any;
};

// Playback Events
export const postPlaybackEvent = async (payload: {
    artist: string;
    song_id?: string;
    completed_ratio?: number;
    country?: string;
    user_id: number;
    device_type?: string;
    source?: string;
}) => {
    const { data } = await backendClient.post('/playback-event', payload);
    return data as { success: boolean };
};

export const canPlaySong = async (songId: string, userId: string) => {
    const { data } = await backendClient.get(`/can-play/${songId}/${userId}`);
    return data as { allowed: boolean };
};

// Error handling
export const handleApiError = (error: any) => {
    if (error.response) {
        const { status, data } = error.response;
        return {
            message: data?.message || data?.detail || `HTTP ${status} error`,
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

// Utility functions
export const getPaymentProviders = () => {
    return [
        { 
            id: 'telebirr', 
            name: 'Telebirr (Legacy)', 
            description: 'Mobile money via USSD',
            status: 'legacy'
        },
        { 
            id: 'telebirr_official', 
            name: 'Telebirr H5', 
            description: 'Official web checkout by Ethiopian Telecom',
            status: 'recommended'
        },
        { 
            id: 'mpesa', 
            name: 'M-Pesa', 
            description: 'Safaricom mobile money',
            status: 'available'
        },
        { 
            id: 'cbe', 
            name: 'CBE Bank', 
            description: 'Commercial Bank of Ethiopia',
            status: 'legacy'
        }
    ];
};

export const formatPrice = (amount: number, currency: string = 'ETB') => {
    return new Intl.NumberFormat('et-ET', {
        style: 'currency',
        currency: currency,
    }).format(amount);
};

// Migration utilities
export const checkBackendHealth = async () => {
    try {
        const { data } = await backendClient.get('/health');
        return {
            status: 'healthy',
            backend_available: true,
            details: data
        };
    } catch (error) {
        return {
            status: 'unhealthy',
            backend_available: false,
            error: handleApiError(error)
        };
    }
};

// Compatibility layer for future migration
export const createPaymentIntent = async (payload: {
    app_name: string;
    object_type: string;
    object_id: string;
    amount: number;
    customer_id: string;
}) => {
    // Map to legacy payment creation
    return createPayment({
        amount: payload.amount,
        method: 'telebirr',
        user_id: payload.customer_id,
        payment_type: payload.object_type,
        playlist_id: payload.object_type === 'playlist' ? payload.object_id : undefined,
        song_id: payload.object_type === 'song' ? payload.object_id : undefined,
    });
};

export const processPayment = async (paymentId: number, payload: {
    payment_provider?: string;
    return_url?: string;
}) => {
    void payload;
    // Map to legacy payment confirmation
    return confirmPayment({
        payment_id: paymentId
    });
};
