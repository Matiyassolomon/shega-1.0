/**
 * useShegaPlayback Hook
 * Integrates Shega backend with Feishin's existing audio player
 * File: src/renderer/hooks/use-shega-playback.ts
 */
import { useEffect, useRef, useCallback, useState } from 'react';
import { shegaApi } from '../api/shega';

interface PlaybackState {
  sessionId: string | null;
  streamUrl: string | null;
  quality: string;
  requiresPayment: boolean;
  paymentOptions: any;
}

export function useShegaPlayback(audioRef: React.RefObject<HTMLAudioElement>) {
  const [state, setState] = useState<PlaybackState>({
    sessionId: null,
    streamUrl: null,
    quality: 'high',
    requiresPayment: false,
    paymentOptions: null,
  });

  const heartbeatInterval = useRef<NodeJS.Timeout | null>(null);
  const deviceId = localStorage.getItem('shega_device_id');

  // Start playback with Shega backend
  const play = useCallback(async (songId?: string) => {
    if (!deviceId) {
      console.error('No device ID - user must login first');
      return;
    }

    try {
      const response = await shegaApi.startPlayback(deviceId, { songId });

      // Handle payment required
      if (response.status === 'PAYMENT_REQUIRED') {
        setState(prev => ({
          ...prev,
          requiresPayment: true,
          paymentOptions: response.purchase_options,
        }));
        return;
      }

      // Set audio source from signed stream endpoint
      if (response.stream?.url && audioRef.current) {
        // The URL is now a signed FastAPI endpoint: /api/v1/playback/stream/{session_id}
        // NOT a raw Navidrome URL
        audioRef.current.src = response.stream.url;
        audioRef.current.play();

        setState({
          sessionId: response.session?.id || null,
          streamUrl: response.stream.url,
          quality: response.stream.quality,
          requiresPayment: false,
          paymentOptions: null,
        });

        // Start heartbeat
        startHeartbeat(response.session?.id);
      }
    } catch (error) {
      console.error('Playback failed:', error);
    }
  }, [deviceId, audioRef]);

  // Send heartbeat every 30 seconds
  const startHeartbeat = useCallback((sessionId: string | undefined) => {
    if (!sessionId || !audioRef.current) return;

    if (heartbeatInterval.current) {
      clearInterval(heartbeatInterval.current);
    }

    heartbeatInterval.current = setInterval(async () => {
      const audio = audioRef.current;
      if (audio && !audio.paused && sessionId) {
        await shegaApi.heartbeat(sessionId, Math.floor(audio.currentTime * 1000));
      }
    }, 30000);
  }, [audioRef]);

  // Stop playback
  const stop = useCallback(async () => {
    if (heartbeatInterval.current) {
      clearInterval(heartbeatInterval.current);
      heartbeatInterval.current = null;
    }

    if (state.sessionId) {
      await shegaApi.stopPlayback(state.sessionId);
    }

    setState(prev => ({
      ...prev,
      sessionId: null,
      streamUrl: null,
    }));
  }, [state.sessionId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (heartbeatInterval.current) {
        clearInterval(heartbeatInterval.current);
      }
    };
  }, []);

  return {
    ...state,
    play,
    stop,
    clearPaymentRequired: () => setState(prev => ({
      ...prev,
      requiresPayment: false,
      paymentOptions: null,
    })),
  };
}
