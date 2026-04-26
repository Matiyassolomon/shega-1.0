# Feishin + FastAPI Backend Integration Guide

## Overview
Integrate Shega's FastAPI backend (payment, playback, recommendations) into Feishin's existing Electron/React frontend without rewriting it.

---

## Feishin Architecture

```
feishin/src/
 main/              # Electron main process
 preload/           # Preload scripts
 renderer/          # React frontend (this is where we integrate)
    api/          # Existing API clients
    components/   # UI components
    store/        # State management (likely Redux/Zustand)
    features/     # Feature modules
    App.tsx       # Main entry
 shared/           # Shared utilities
 types/            # TypeScript types
```

---

## Integration Points

### 1. API Layer Extension

**Location:** `src/renderer/api/`

Instead of creating new API files, extend Feishin's existing API client:

```typescript
// src/renderer/api/shega.ts
// Extend Feishin's existing axios instance

import { api } from './api'; // Feishin's existing client

export const shegaApi = {
  // Auth - extend existing auth
  auth: {
    async getToken(credentials: { email: string; password: string }) {
      const response = await api.post('/auth/login', credentials, {
        headers: {
          'X-Device-Name': navigator.platform,
          'X-Device-Type': /Mobi/.test(navigator.userAgent) ? 'mobile' : 'desktop',
        },
      });
      return response.data;
    },
  },

  // Playback - integrate with Feishin's player
  playback: {
    async start(deviceId: string, networkType: 'wifi' | 'mobile' = 'wifi') {
      return api.post('/play/start', {
        device_id: deviceId,
        network_type: networkType,
      });
    },

    async heartbeat(sessionId: string, positionMs: number) {
      return api.post('/play/heartbeat', {
        session_id: sessionId,
        position_ms: positionMs,
      });
    },
  },

  // Payment - NEW feature
  payment: {
    async checkAccess(songId: string) {
      return api.get(`/user/library/check?song_id=${songId}`);
    },

    async createIntent(songId: string) {
      return api.post('/payments/song-purchase', { song_id: songId });
    },
  },

  // Recommendations
  recommendations: {
    async getNext(userId: string, currentSongId?: string) {
      return api.get('/recommendations/next', {
        params: { user_id: userId, current_song_id: currentSongId },
      });
    },
  },
};
```

---

### 2. Player Integration

**Location:** Find Feishin's existing player component (likely in `src/renderer/components/player/` or `src/renderer/features/player/`)

Hook into their player events:

```typescript
// In Feishin's existing player component
import { useEffect } from 'react';
import { shegaApi } from '../../api/shega';

// Hook into Feishin's existing audio player
useEffect(() => {
  const audio = audioRef.current;
  if (!audio) return;

  // Send heartbeat every 30 seconds
  const interval = setInterval(async () => {
    if (sessionId && !audio.paused) {
      await shegaApi.playback.heartbeat(
        sessionId,
        Math.floor(audio.currentTime * 1000)
      );
    }
  }, 30000);

  return () => clearInterval(interval);
}, [sessionId]);

// Handle PAYMENT_REQUIRED from backend
useEffect(() => {
  const handleError = async (error: any) => {
    if (error.response?.data?.status === 'PAYMENT_REQUIRED') {
      // Show payment modal using Feishin's UI system
      showPaymentModal(error.response.data);
    }
  };
  // ...attach to error handler
}, []);
```

---

### 3. Payment Modal (New Component)

**Location:** `src/renderer/components/`

Create minimal payment modal that matches Feishin's design:

```typescript
// src/renderer/components/payment-modal.tsx
import React from 'react';
import { shegaApi } from '../api/shega';

export const PaymentModal: React.FC<{
  song: any;
  options: any;
  onClose: () => void;
}> = ({ song, options, onClose }) => {
  const handlePurchase = async () => {
    const intent = await shegaApi.payment.createIntent(song.id);
    // Open external browser for payment
    window.open(intent.redirect_url, '_blank');
  };

  // Use Feishin's existing modal styling
  return (
    <div className="feishin-modal payment-modal">
      {/* Match Feishin's CSS classes */}
      <h3>{song.title}</h3>
      <p>Preview: {song.preview_url}</p>
      <button onClick={handlePurchase}>
        Buy for {options.individual.price} {options.individual.currency}
      </button>
      <button onClick={onClose}>Close</button>
    </div>
  );
};
```

---

### 4. Store/State Integration

**Location:** `src/renderer/store/` (likely Redux or Zustand)

Extend existing store with Shega-specific state:

```typescript
// Add to existing store
interface ShegaState {
  deviceId: string | null;
  sessionId: string | null;
  accessType: 'free' | 'purchase' | 'subscription' | null;
  requiresPayment: boolean;
  paymentOptions: any;
}

// Actions
const useShegaStore = create((set) => ({
  // ...existing Feishin state

  // Shega additions
  setDeviceId: (id: string) => set({ deviceId: id }),
  setSession: (sessionId: string) => set({ sessionId }),
  setPaymentRequired: (options: any) => set({
    requiresPayment: true,
    paymentOptions: options,
  }),
  clearPaymentRequired: () => set({
    requiresPayment: false,
    paymentOptions: null,
  }),
}));
```

---

### 5. Configuration

**Location:** Feishin's config files

Update Feishin's config to point to our backend:

```typescript
// In Feishin's config/env files
const SHEGA_API_URL = process.env.SHEGA_API_URL || 'http://localhost:8000/api/v1';
const NAVIDROME_URL = process.env.NAVIDROME_URL || 'http://localhost:4533';

// Modify Feishin's existing API base URL
export const api = axios.create({
  baseURL: SHEGA_API_URL,  // Point to FastAPI instead of Navidrome
  // ...existing config
});
```

---

### 6. Quality Selector (Extend Existing UI)

Find Feishin's settings/preferences and add quality selector:

```typescript
// In Feishin's existing settings component
export const AudioSettings: React.FC = () => {
  // ...existing Feishin settings

  // Add Shega quality selector
  const [quality, setQuality] = useState('high');

  return (
    <div className="settings-section">
      <h3>Audio Quality</h3>
      <select value={quality} onChange={(e) => setQuality(e.target.value)}>
        <option value="low">Data Saver (64 kbps)</option>
        <option value="medium">Standard (128 kbps)</option>
        <option value="high">High Quality (320 kbps)</option>
        <option value="lossless">Lossless (1411 kbps)</option>
      </select>
      <p>Current: {currentQuality}  {qualityReason}</p>
    </div>
  );
};
```

---

## Integration Steps

### Step 1: Map Feishin's Structure
```bash
cd feishin
# Find existing API layer
find src -name "*.ts" -path "*/api/*" | head -10

# Find player components
grep -r "audio" src/renderer/components --include="*.tsx" -l

# Find state management
grep -r "create\|redux\|zustand" src --include="*.ts" -l
```

### Step 2: Extend (Don't Replace)

```bash
# Add new file
src/renderer/api/shega.ts       # Extend existing API
src/renderer/components/payment-modal.tsx  # New component

# Modify existing files minimally
src/renderer/store/index.ts     # Add Shega state
src/renderer/components/player.tsx  # Add heartbeat hook
```

### Step 3: Environment Variables

Add to Feishin's `.env`:
```env
SHEGA_API_URL=http://localhost:8000/api/v1
NAVIDROME_URL=http://localhost:4533
ENABLE_PAYMENTS=true
```

---

## Testing Integration

```bash
# 1. Start backend
cd backend && uvicorn app.main:app --reload

# 2. Start Navidrome
docker start navidrome

# 3. Start Feishin (modified)
cd feishin && npm run dev

# 4. Test flow
# - Login via Feishin  hits /auth/login
# - Play song  hits /play/start
# - Payment required  shows modal
# - Heartbeat  every 30 seconds
```

---

## Key Principles

 **DO:**
- Extend existing API client
- Hook into existing player events
- Use Feishin's existing UI components/styling
- Add minimal new files
- Reuse Feishin's state management

 **DON'T:**
- Create parallel API layer
- Replace Feishin's player
- Rewrite authentication
- Create new folder structure
- Break existing Navidrome integration

---

## Summary

Instead of rebuilding Feishin, we:
1. **Extend** its existing API client with Shega endpoints
2. **Hook** our playback session into its player lifecycle
3. **Add** payment modal using its UI system
4. **Configure** it to use our FastAPI backend

Result: Feishin + Shega backend = Spotify-like experience with payments.
