import { useQuery } from '@tanstack/react-query';

import { getRecentlyPlayed, type RecentlyPlayedSong } from '../client';
import { getBackendUserId } from '../client';

export const useRecentlyPlayed = (hours: number = 24, limit: number = 20) => {
    const userId = getBackendUserId();

    return useQuery({
        queryKey: ['recently-played', userId, hours, limit],
        queryFn: async (): Promise<RecentlyPlayedSong[]> => {
            if (!userId) {
                throw new Error('User not authenticated');
            }
            return await getRecentlyPlayed(userId, hours, limit);
        },
        enabled: !!userId,
        staleTime: 2 * 60 * 1000, // 2 minutes
        gcTime: 5 * 60 * 1000, // 5 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};
