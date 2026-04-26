/**
 * Shega API Integration
 * Extends Feishin's existing API client
 * File: src/renderer/api/shega.ts
 */
import axios from 'axios';

// Use Feishin's existing axios config as base
const SHEGA_BASE_URL = import.meta.env.SHEGA_API_URL || 'http://localhost:8000/api/v1';

// Create client that matches Feishin's pattern
const shegaClient = axios.create({
  baseURL: SHEGA_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add JWT
shegaClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('shega_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  // Add device info
  const deviceId = localStorage.getItem('shega_device_id');
  if (deviceId) {
    config.headers['X-Device-Id'] = deviceId;
  }
  return config;
});

// Response interceptor - handle PAYMENT_REQUIRED
shegaClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data?.status === 'PAYMENT_REQUIRED') {
      // Emit event for Feishin's UI to catch
      window.dispatchEvent(new CustomEvent('shega:payment-required', {
        detail: error.response.data
      }));
    }
    return Promise.reject(error);
  }
);

// Shega API methods
export const shegaApi = {
  // Auth
  setToken(token: string) {
    localStorage.setItem('shega_token', token);
  },
  
  setDeviceId(deviceId: string) {
    localStorage.setItem('shega_device_id', deviceId);
  },

  // Playback - uses /playback/start (orchestration endpoint)
  async startPlayback(deviceId: string, options: any = {}) {
    const response = await shegaClient.post('/playback/start', {
      device_id: deviceId,
      current_song_id: options.songId,
      network_type: options.networkType || 'wifi',
    }, {
      headers: {
        'X-Network-Type': options.networkType || 'wifi',
        'X-Network-Quality': options.networkQuality || '1.0',
      }
    });
    return response.data;
  },

  async heartbeat(sessionId: string, positionMs: number) {
    return shegaClient.post('/playback/heartbeat', {
      session_id: sessionId,
      position_ms: positionMs,
    });
  },

  async stopPlayback(sessionId: string) {
    return shegaClient.post('/playback/stop', { session_id: sessionId });
  },

  // Get stream URL from signed endpoint (not raw Navidrome URL)
  async getStreamUrl(sessionId: string) {
    return shegaClient.get(`/playback/stream/${sessionId}`);
  },

  async getPreviewStream(songId: string) {
    return shegaClient.get(`/playback/stream/preview/${songId}`);
  },

  // Payment
  async checkAccess(songId: string) {
    return shegaClient.get(`/user/library/check?song_id=${songId}`);
  },

  async createPaymentIntent(songId: string) {
    return shegaClient.post('/payments/song-purchase', { song_id: songId });
  },

  // Recommendations - home feed endpoints
  async getNextSong(userId: string, currentSongId?: string) {
    return shegaClient.get('/recommendations/next', {
      params: { user_id: userId, current_song_id: currentSongId },
    });
  },

  async getTopFeed(location: string, limit: number = 20) {
    return shegaClient.get('/recommendations/feed/top', {
      params: { location, limit },
    });
  },

  async getTrendingFeed(location: string, limit: number = 20) {
    return shegaClient.get('/recommendations/feed/trending', {
      params: { location, limit },
    });
  },

  async getForYouFeed(limit: number = 20) {
    return shegaClient.get('/recommendations/feed/for-you', {
      params: { limit },
    });
  },

  async getFriendsFeed(limit: number = 20) {
    return shegaClient.get('/recommendations/feed/friends', {
      params: { limit },
    });
  },
};

export default shegaApi;
