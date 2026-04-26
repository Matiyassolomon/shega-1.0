import { openModal } from '@mantine/modals';
import { useEffect, useMemo, useRef, useState } from 'react';

import { api } from '/@/renderer/api';
import { startPlayback, playbackHeartbeat, stopPlayback, getBackendUserId } from '/@/renderer/api/client';
import { TranscodingConfig } from '/@/renderer/store';
import { Text } from '/@/shared/components/text/text';
import { toast } from '/@/shared/components/toast/toast';
import { QueueSong } from '/@/shared/types/domain-types';

// Store active session for heartbeat management
const activeSession = {
    sessionId: null as string | null,
    heartbeatInterval: null as NodeJS.Timeout | null,
};

const startSessionHeartbeat = (sessionId: string, audioElement: HTMLAudioElement | null) => {
    // Clear any existing heartbeat
    if (activeSession.heartbeatInterval) {
        clearInterval(activeSession.heartbeatInterval);
    }
    
    activeSession.sessionId = sessionId;
    
    // Send heartbeat every 30 seconds while playing
    activeSession.heartbeatInterval = setInterval(async () => {
        if (audioElement && !audioElement.paused && activeSession.sessionId) {
            const positionMs = Math.floor(audioElement.currentTime * 1000);
            try {
                await playbackHeartbeat(activeSession.sessionId, positionMs);
            } catch (err) {
                console.error('Heartbeat failed:', err);
            }
        }
    }, 30000);
};

const stopSessionHeartbeat = async () => {
    if (activeSession.heartbeatInterval) {
        clearInterval(activeSession.heartbeatInterval);
        activeSession.heartbeatInterval = null;
    }
    
    if (activeSession.sessionId) {
        try {
            await stopPlayback(activeSession.sessionId);
        } catch (err) {
            console.error('Failed to stop playback session:', err);
        }
        activeSession.sessionId = null;
    }
};

const resetPlaybackState = () => {
    activeSession.sessionId = null;
};

export function useSongUrl(
    song: QueueSong | undefined,
    current: boolean,
    transcode: TranscodingConfig,
): string | undefined {
    void transcode;
    const prior = useRef(['', '']);
    const [streamUrl, setStreamUrl] = useState<string | undefined>(undefined);
    const [paymentRequired, setPaymentRequired] = useState(false);

    useEffect(() => {
        let mounted = true;

        const orchestratePlayback = async () => {
            if (!song) {
                // Stop any active session when no song
                await stopSessionHeartbeat();
                resetPlaybackState();
                if (mounted) setStreamUrl(undefined);
                return;
            }

            try {
                await stopSessionHeartbeat();
                const userId = getBackendUserId();
                
                // Call atomic playback orchestration endpoint
                // This combines access check + stream URL issuance in one call
                const result = await startPlayback({
                    device_id: `device_${userId}`, // TODO: Use real device registration
                    current_song_id: song.id,
                    network_type: 'wifi',
                    network_quality: 1.0,
                });

                if (!mounted) return;

                if (result.status === 'PAYMENT_REQUIRED') {
                    setPaymentRequired(true);
                    setStreamUrl(undefined);
                    resetPlaybackState();
                    
                    openModal({
                        children: <Text>Buy this song or subscribe to unlock playback.</Text>,
                        title: 'Playback Locked',
                    });
                    toast.warn({
                        message: result.message || 'Purchase or subscription required',
                        title: 'Playback',
                    });
                    return;
                }

                if (result.status === 'PLAYING' && result.stream?.url) {
                    setPaymentRequired(false);
                    
                    // The URL is a SIGNED media access URL: /api/v1/playback/media?token=<jwt>
                    // Backend validates the token and returns HTTP 307 redirect to Navidrome.
                    // Audio bytes flow directly from Navidrome → Client. API server is NOT
                    // the media transport bottleneck. The token is short-lived (5 min TTL).
                    setStreamUrl(result.stream.url);
                    
                    // Start heartbeat for this session
                    if (result.session?.id) {
                        // Store session for heartbeat - we'll start heartbeat when audio plays
                        activeSession.sessionId = result.session.id;
                    }
                }
            } catch (error: unknown) {
                console.error('Playback orchestration failed:', error);
                toast.error({
                    message: error instanceof Error ? error.message : 'Playback failed',
                    title: 'Playback',
                });
                resetPlaybackState();
                if (mounted) setStreamUrl(undefined);
            }
        };

        orchestratePlayback();
        
        return () => {
            mounted = false;
        };
    }, [song, song?._uniqueId, song?.id]);

    // Start heartbeat when audio actually starts playing
    useEffect(() => {
        const audio = document.querySelector('audio');
        if (audio && streamUrl && activeSession.sessionId) {
            const handlePlay = () => {
                startSessionHeartbeat(activeSession.sessionId!, audio);
            };
            const handlePause = () => {
                // Heartbeat continues but we could optimize here
            };
            const handleEnded = async () => {
                await stopSessionHeartbeat();
            };

            audio.addEventListener('play', handlePlay);
            audio.addEventListener('pause', handlePause);
            audio.addEventListener('ended', handleEnded);

            return () => {
                audio.removeEventListener('play', handlePlay);
                audio.removeEventListener('pause', handlePause);
                audio.removeEventListener('ended', handleEnded);
            };
        }
        return undefined;
    }, [streamUrl]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            stopSessionHeartbeat();
        };
    }, []);

    return useMemo(() => {
        if (paymentRequired) {
            return undefined;
        }

        if (!streamUrl) {
            prior.current = ['', ''];
            return undefined;
        }

        if (song?._uniqueId) {
            // If we are the current track, we do not want a transcoding
            // reconfiguration to force a restart.
            if (current && prior.current[0] === song._uniqueId) {
                return prior.current[1];
            }

            // The streamUrl is already the signed FastAPI endpoint
            // No need to build Navidrome URL anymore
            prior.current = [song._uniqueId, streamUrl];
            return streamUrl;
        }

        prior.current = ['', ''];
        return undefined;
    }, [
        paymentRequired,
        streamUrl,
        song?._uniqueId,
        current,
    ]);
}

// Legacy function for direct Navidrome access (deprecated)
// Use orchestrated playback via useSongUrl instead
export const getSongUrl = (song: QueueSong, transcode: TranscodingConfig) => {
    return api.controller.getStreamUrl({
        apiClientProps: { serverId: song._serverId },
        query: {
            bitrate: transcode.bitrate,
            format: transcode.format,
            id: song.id,
            transcode: transcode.enabled,
        },
    });
};
