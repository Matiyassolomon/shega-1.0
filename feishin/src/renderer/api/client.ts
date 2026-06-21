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

export const getBackendUserId = (): string | null => {
    const userId = localStorage.getItem(BACKEND_USER_ID_STORAGE_KEY);
    return userId || null;
};
export const getBackendAccessToken = () =>
    localStorage.getItem(BACKEND_ACCESS_TOKEN_STORAGE_KEY) || '';

export const setBackendUserId = (userId: number | string) => {
    localStorage.setItem(BACKEND_USER_ID_STORAGE_KEY, String(userId));
};

export const setBackendAccessToken = (token: string) => {
    localStorage.setItem(BACKEND_ACCESS_TOKEN_STORAGE_KEY, token);
};

export const clearBackendAuth = (): void => {
    localStorage.removeItem(BACKEND_USER_ID_STORAGE_KEY);
    localStorage.removeItem(BACKEND_ACCESS_TOKEN_STORAGE_KEY);
};

export const isBackendAuthenticated = (): boolean => {
    const userId = getBackendUserId();
    const token = getBackendAccessToken();
    return !!(userId && token);
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

export interface RecentlyPlayedSong {
    song_id: number;
    title: string;
    artist: string;
    album?: string | null;
    genre?: string | null;
    cover_art?: string | null;
    last_played: string | null;
    play_count: number;
}

export const getRecentlyPlayed = async (userId: string, hours: number = 24, limit: number = 20) => {
    const { data } = await backendClient.get(`/users/${userId}/recently-played`, {
        params: { hours, limit },
    });
    return data as RecentlyPlayedSong[];
};

export const getLikedSongs = async (userId: string, limit: number = 50) => {
    const { data } = await backendClient.get(`/users/${userId}/liked-songs`, {
        params: { limit },
    });
    return data as RecentlyPlayedSong[];
};

export interface ArtistSong {
    song_id: number;
    title: string;
    artist: string;
    genre: string;
    play_count: number;
    like_count: number;
    cover_art?: string | null;
}

export interface ArtistAlbum {
    name: string;
    song_count: number;
    cover_art?: string | null;
}

export interface ArtistProfile {
    artist_name: string;
    total_songs: number;
    total_plays: number;
    total_likes: number;
    genres: string[];
    top_songs: ArtistSong[];
    albums: ArtistAlbum[];
}

export const getArtistProfile = async (artistName: string) => {
    const { data } = await backendClient.get(`/users/artists/${encodeURIComponent(artistName)}`);
    return data as ArtistProfile;
};

export interface ArtistDashboard {
    total_earnings: number;
    total_plays: number;
    total_likes: number;
    total_songs: number;
    recent_plays: number;
    recent_earnings: number;
}

export const getArtistDashboard = async (userId: string) => {
    const { data } = await backendClient.get(`/users/${userId}/artist-dashboard`);
    return data as ArtistDashboard;
};

export interface WalletTransaction {
    id: string;
    type: 'credit' | 'debit';
    amount: number;
    description: string;
    created_at: string;
}

export interface Wallet {
    balance: number;
    currency: string;
    transactions: WalletTransaction[];
}

export const getWallet = async (userId: string) => {
    const { data } = await backendClient.get(`/users/${userId}/wallet`);
    return data as Wallet;
};

export interface PayoutRequest {
    id: string;
    user_id: number;
    amount: number;
    bank_account: string;
    bank_name: string;
    status: 'pending' | 'approved' | 'rejected' | 'completed';
    created_at: string;
}

export interface PayoutRequestCreate {
    amount: number;
    bank_account: string;
    bank_name: string;
}

export const createPayoutRequest = async (userId: string, request: PayoutRequestCreate) => {
    const { data } = await backendClient.post(`/users/${userId}/payout-requests`, request);
    return data as PayoutRequest;
};

export const getPayoutRequests = async (userId: string) => {
    const { data } = await backendClient.get(`/users/${userId}/payout-requests`);
    return data as PayoutRequest[];
};

export interface AdEvent {
    id: string;
    user_id: number;
    event_type: 'play' | 'complete' | 'skip';
    ad_id: string;
    song_id: string;
    duration: number;
    timestamp: string;
}

export const trackAdEvent = async (
    userId: string,
    eventType: 'play' | 'complete' | 'skip',
    adId: string,
    songId: string,
    duration?: number,
) => {
    const { data } = await backendClient.post(`/users/${userId}/ad-events`, {
        event_type: eventType,
        ad_id: adId,
        song_id: songId,
        duration: duration || 0,
    });
    return data as AdEvent;
};

export interface AdRevenue {
    total_revenue: number;
    total_impressions: number;
    total_completions: number;
    revenue_per_impression: number;
    recent_revenue: number;
}

export const getAdRevenue = async (userId: string) => {
    const { data } = await backendClient.get(`/users/${userId}/ad-revenue`);
    return data as AdRevenue;
};

export interface RecommendationAnalytics {
    user_id: number;
    total_recommendations_shown: number;
    recommendation_click_rate: number;
    average_session_length: number;
    top_genres: string[];
    recommendation_sources: {
        collaborative: number;
        content_based: number;
        trending: number;
        random: number;
    };
}

export const getRecommendationAnalytics = async (userId: string) => {
    const { data } = await backendClient.get(`/recommendations/analytics`, {
        params: { user_id: userId },
    });
    return data as RecommendationAnalytics;
};

export interface RecommendationReason {
    factor: string;
    confidence: number;
    description: string;
}

export interface RecommendationExplanation {
    user_id: number;
    song_id: string;
    song_title: string;
    artist: string;
    recommendation_reasons: RecommendationReason[];
    overall_confidence: number;
}

export const explainRecommendation = async (userId: string, songId: string) => {
    const { data } = await backendClient.get(`/recommendations/explain`, {
        params: { user_id: userId, song_id: songId },
    });
    return data as RecommendationExplanation;
};

export interface SearchSuggestion {
    type: 'song' | 'artist';
    text: string;
    artist?: string;
    relevance: number;
}

export interface SearchAutocompleteResponse {
    suggestions: SearchSuggestion[];
}

export const searchAutocomplete = async (query: string, limit: number = 10) => {
    const { data } = await backendClient.get('/search/autocomplete', {
        params: { query, limit },
    });
    return data as SearchAutocompleteResponse;
};

export interface SearchResult {
    song_id: string;
    title: string;
    artist: string;
    genre: string;
    play_count_7d: number;
    like_count_7d: number;
    cover_art_path: string | null;
    relevance_score: number;
}

export interface SearchResponse {
    query: string;
    total: number;
    offset: number;
    limit: number;
    sort_by: string;
    results: SearchResult[];
}

export const searchSongs = async (
    query: string,
    limit: number = 20,
    offset: number = 0,
    sortBy: 'relevance' | 'popularity' | 'recent' = 'relevance',
) => {
    const { data } = await backendClient.get('/search/songs', {
        params: { query, limit, offset, sort_by: sortBy },
    });
    return data as SearchResponse;
};

export interface ArtistSearchResult {
    artist: string;
    song_count: number;
    total_plays: number;
    relevance_score: number;
}

export interface ArtistSearchResponse {
    query: string;
    results: ArtistSearchResult[];
}

export const searchArtists = async (query: string, limit: number = 20) => {
    const { data } = await backendClient.get('/search/artists', {
        params: { query, limit },
    });
    return data as ArtistSearchResponse;
};

export interface AdminDashboard {
    total_users: number;
    total_artists: number;
    total_songs: number;
    total_plays: number;
    total_likes: number;
    total_revenue: number;
    active_subscriptions: number;
    pending_payouts: number;
    recent_signups: number;
}

export const getAdminDashboard = async () => {
    const { data } = await backendClient.get('/users/admin/dashboard');
    return data as AdminDashboard;
};

export interface AdminUser {
    id: number;
    username: string;
    email: string;
    created_at: string;
    is_active: boolean;
    subscription_status: string;
}

export interface AdminUsersResponse {
    total: number;
    offset: number;
    limit: number;
    users: AdminUser[];
}

export const getAdminUsers = async (limit: number = 20, offset: number = 0) => {
    const { data } = await backendClient.get('/users/admin/users', {
        params: { limit, offset },
    });
    return data as AdminUsersResponse;
};

export interface AdminArtist {
    id: number;
    name: string;
    song_count: number;
    total_plays: number;
    total_revenue: number;
    verified: boolean;
}

export interface AdminArtistsResponse {
    total: number;
    offset: number;
    limit: number;
    artists: AdminArtist[];
}

export const getAdminArtists = async (limit: number = 20, offset: number = 0) => {
    const { data } = await backendClient.get('/users/admin/artists', {
        params: { limit, offset },
    });
    return data as AdminArtistsResponse;
};

export interface AdminPayment {
    id: string;
    user_id: number;
    amount: number;
    currency: string;
    status: string;
    payment_type: string;
    created_at: string;
}

export interface AdminPaymentsResponse {
    total: number;
    offset: number;
    limit: number;
    payments: AdminPayment[];
}

export const getAdminPayments = async (
    limit: number = 20,
    offset: number = 0,
    status?: string,
) => {
    const { data } = await backendClient.get('/users/admin/payments', {
        params: { limit, offset, status },
    });
    return data as AdminPaymentsResponse;
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
