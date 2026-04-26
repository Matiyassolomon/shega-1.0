import axios from 'axios';

const backendBaseUrl =
    ((import.meta as any).env?.BACKEND_API as string | undefined) ||
    ((import.meta as any).env?.VITE_BACKEND_API as string | undefined) ||
    'http://localhost:8000';

export const backendClient = axios.create({
    baseURL: backendBaseUrl,
    timeout: 10000,
});

export type DeviceClass = 'high' | 'lite';
export const BACKEND_USER_ID_STORAGE_KEY = 'backend-user-id';
export const BACKEND_ACCESS_TOKEN_STORAGE_KEY = 'backend-access-token';

export const getBackendUserId = () => localStorage.getItem(BACKEND_USER_ID_STORAGE_KEY) || '1';
export const getBackendAccessToken = () =>
    localStorage.getItem(BACKEND_ACCESS_TOKEN_STORAGE_KEY) || '';

export const setBackendUserId = (userId: number | string) => {
    localStorage.setItem(BACKEND_USER_ID_STORAGE_KEY, String(userId));
};

export const setBackendAccessToken = (token: string) => {
    localStorage.setItem(BACKEND_ACCESS_TOKEN_STORAGE_KEY, token);
};

backendClient.interceptors.request.use((config) => {
    const token = getBackendAccessToken();

    if (token) {
        config.headers = config.headers ?? {};
        config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
});

export interface MarketplacePlaylist {
    artist_name?: null | string;
    artist_verified: boolean;
    cover_art_path?: null | string;
    creator_name: string;
    price: number;
    currency: string;
    playlist_id: string;
    preview_song_id?: null | string;
    region?: null | string;
    sales_count: number;
    save_count: number;
    save_rate: number;
    share_count: number;
    social_score: number;
    title: string;
}

export interface MarketplaceSong {
    artist: string;
    cover_art_path?: null | string;
    currency: string;
    genre: string;
    is_premium: boolean;
    like_count_7d: number;
    play_count_7d: number;
    price: number;
    sales_count: number;
    song_id: string;
    title: string;
}

export interface TasteVector {
    acoustic_signature: Record<string, number>;
    average_tempo: number;
    genre_affinity: Record<string, number>;
    qenet_mode_affinity: Record<string, number>;
}

export interface RecommendationSong {
    artist: string;
    country?: null | string;
    genre: string;
    qenet_mode?: null | string;
    score: number;
    score_breakdown: Record<string, number>;
    song_id: string;
    title: string;
}

export interface LookalikeUser {
    similarity: number;
    user_id: number;
}

export interface RecommendationPayload {
    location?: null | string;
    lookalike_audience: LookalikeUser[];
    model_backend: string;
    recommendations: RecommendationSong[];
    taste_vector: TasteVector;
    user_id: number;
}

export interface TrendingSong {
    artist: string;
    country?: null | string;
    genre: string;
    hot_score: number;
    momentum_score: number;
    qenet_mode?: null | string;
    regional_boost: number;
    social_proof: number;
    song_id: string;
    title: string;
}

export interface TrendingPayload {
    generated_at: string;
    location?: null | string;
    recommendations: TrendingSong[];
}

export interface UserProfile {
    active_subscription: boolean;
    created_at: string;
    device_class: DeviceClass;
    email?: null | string;
    expires_at?: null | string;
    id: number;
    is_telegram_user: boolean;
    lookalike_audience: LookalikeUser[];
    preferred_location?: null | string;
    recent_playback_count: number;
    secure_playlist_ids: string[];
    subscription_status: 'active' | 'expired';
    taste_vector: TasteVector;
    telegram_id?: null | string;
}

export const getUserProfile = async (userId: string) => {
    const { data } = await backendClient.get(`/users/${userId}/profile`);
    return data as UserProfile;
};

export const checkSubscription = async (userId: string) => {
    const { data } = await backendClient.get('/subscription/check', {
        params: { user_id: userId },
    });
    return data as { subscribed: boolean };
};

export const getMarketplacePlaylists = async () => {
    const { data } = await backendClient.get('/marketplace/playlists');
    return data as MarketplacePlaylist[];
};

export const getMarketplaceSongs = async () => {
    const { data } = await backendClient.get('/marketplace/songs');
    return data as MarketplaceSong[];
};

export const purchasePlaylist = async (userId: string, playlistId: string) => {
    const { data } = await backendClient.post('/marketplace/buy', {
        buyer_id: Number(userId),
        playlist_id: playlistId,
    });
    return data;
};

export const purchaseSong = async (userId: string, songId: string) => {
    const { data } = await backendClient.post('/marketplace/buy-song', {
        buyer_id: Number(userId),
        song_id: songId,
    });
    return data as { buyer_id: number; purchased: boolean; sales_count: number; song_id: string };
};

export const savePlaylist = async (userId: string, playlistId: string) => {
    const { data } = await backendClient.post('/marketplace/save-playlist', {
        playlist_id: playlistId,
        user_id: Number(userId),
    });
    return data as { playlist_id: string; save_count: number; saved: boolean };
};

export const getSecurePlaylistAccess = async (userId: string, playlistId: string) => {
    const { data } = await backendClient.get(`/marketplace/secure-access/${playlistId}`, {
        params: { user_id: Number(userId) },
    });
    return data as {
        art_path?: null | string;
        authorized: boolean;
        playlist_id: string;
        stream_path?: null | string;
        x_accel_redirect?: null | string;
    };
};

export const getSecureSongAccess = async (userId: string, songId: string) => {
    const { data } = await backendClient.get(`/marketplace/secure-song-access/${songId}`, {
        params: { user_id: Number(userId) },
    });
    return data as {
        art_path?: null | string;
        authorized: boolean;
        song_id: string;
        stream_path?: null | string;
    };
};

export const canPlaySong = async (userId: string, songId: string) => {
    const { data } = await backendClient.get(`/can-play/${songId}/${userId}`);
    return data as { allowed: boolean };
};

export interface PlaybackStartResponse {
    status: 'PLAYING' | 'PAYMENT_REQUIRED';
    song?: {
        id: string;
        title: string;
        artist: string;
        album?: string;
        duration?: number;
        album_art?: string;
    };
    stream?: {
        url: string;
        quality: string;
        bitrate: number;
        codec: string;
        quality_reason: string;
        can_upgrade: boolean;
    };
    session?: {
        id: string;
        started_at: string;
        expires_at: string;
    };
    access?: {
        type: string;
        is_owned: boolean;
    };
    limits?: {
        max_concurrent_streams: number;
        current_active_streams: number;
        remaining_streams: number;
    };
    message?: string;
    song_preview?: {
        id: string;
        title: string;
        artist: string;
        preview_url: string;
        preview_duration: number;
    };
    purchase_options?: {
        individual: {
            price: number;
            currency: string;
            purchase_url: string;
        };
        subscription: {
            available: boolean;
            tiers: string[];
            upgrade_url: string;
        };
    };
}

export const startPlayback = async (payload: {
    device_id: string;
    current_song_id?: string;
    network_type?: string;
    network_quality?: number;
}) => {
    const { data } = await backendClient.post<PlaybackStartResponse>('/playback/start', payload, {
        headers: {
            'X-Network-Type': payload.network_type || 'wifi',
            'X-Network-Quality': String(payload.network_quality || 1.0),
        },
    });
    return data;
};

export const playbackHeartbeat = async (sessionId: string, positionMs: number) => {
    const { data } = await backendClient.post('/playback/heartbeat', {
        session_id: sessionId,
        position_ms: positionMs,
    });
    return data as { ok: boolean; session_active: boolean };
};

export const stopPlayback = async (sessionId: string) => {
    const { data } = await backendClient.post('/playback/stop', { session_id: sessionId });
    return data as { stopped: boolean; session_id: string };
};

export const createPayment = async (payload: {
    amount: number;
    method: 'cbe' | 'telebirr';
    playlist_id?: string;
    type: 'playlist_purchase' | 'song_purchase' | 'subscription_monthly' | 'wallet_topup';
    user_id: string;
}) => {
    const { data } = await backendClient.post('/payment/create', {
        amount: payload.amount,
        method: payload.method,
        payment_type: payload.type,
        playlist_id: payload.playlist_id,
        user_id: Number(payload.user_id),
    });
    return data as {
        amount: number;
        created_at: string;
        id: number;
        payment_type?: null | string;
        playlist_id?: null | string;
        status: 'confirmed' | 'pending';
        user_id: number;
    };
};

export const getRecommendations = async (userId: string, location?: string) => {
    const { data } = await backendClient.get('/recommendations/for-you', {
        params: { location, user_id: Number(userId) },
    });
    return data as RecommendationPayload;
};

export const getTrending = async (location?: string) => {
    const { data } = await backendClient.get('/recommendations/trending', {
        params: { location },
    });
    return data as TrendingPayload;
};

export const registerDevice = async (payload: {
    email?: string;
    telegram?: boolean;
    telegram_id?: string;
    user_agent: string;
}) => {
    const { data } = await backendClient.post('/register-device', payload);
    return data as {
        access_token: string;
        device_class: DeviceClass;
        token_type: 'bearer';
        user_id: number;
    };
};

export const postPlaybackEvent = async (payload: {
    artist: string;
    completed_ratio?: number;
    country?: string;
    duration?: number;
    extracted_features?: Record<string, unknown>;
    genre?: string;
    is_looped?: boolean;
    language?: string;
    location?: string;
    played_seconds?: number;
    playlist_id?: string;
    qenet_mode?: string;
    release_date?: string;
    skipped?: boolean;
    song_id: string;
    tempo?: number;
    title: string;
}) => {
    const { data } = await backendClient.post('/engagement/playback', payload);
    return data as {
        recorded: boolean;
        song_id: string;
        updated_taste_vector: TasteVector;
        user_id: number;
    };
};

export const telegramLogin = async (payload: { telegram_user_id: string }) => {
    return {
        skipped: true,
        telegram_user_id: payload.telegram_user_id,
    };
};
