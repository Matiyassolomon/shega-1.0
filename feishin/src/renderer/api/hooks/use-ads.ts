import { useMutation, useQuery } from '@tanstack/react-query';

import {
    trackAdEvent,
    getAdRevenue,
    type AdEvent,
    type AdRevenue,
} from '../client';

export const useTrackAdEvent = () => {
    return useMutation({
        mutationFn: async (params: {
            userId: string;
            eventType: 'play' | 'complete' | 'skip';
            adId: string;
            songId: string;
            duration?: number;
        }): Promise<AdEvent> => {
            return await trackAdEvent(
                params.userId,
                params.eventType,
                params.adId,
                params.songId,
                params.duration,
            );
        },
    });
};

export const useAdRevenue = (userId: string) => {
    return useQuery({
        queryKey: ['ad-revenue', userId],
        queryFn: async (): Promise<AdRevenue> => {
            return await getAdRevenue(userId);
        },
        enabled: !!userId,
        staleTime: 5 * 60 * 1000, // 5 minutes
        gcTime: 10 * 60 * 1000, // 10 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};
