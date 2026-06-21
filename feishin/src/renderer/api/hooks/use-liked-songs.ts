import { useQuery } from '@tanstack/react-query';

import { getLikedSongs, type RecentlyPlayedSong } from '../client';
import { getBackendUserId } from '../client';

export const useLikedSongs = (limit: number = 50) => {
    const userId = getBackendUserId();

    return useQuery({
        queryKey: ['liked-songs', userId, limit],
        queryFn: async (): Promise<RecentlyPlayedSong[]> => {
            if (!userId) {
                throw new Error('User not authenticated');
            }
            return await getLikedSongs(userId, limit);
        },
        enabled: !!userId,
        staleTime: 5 * 60 * 1000, // 5 minutes
        gcTime: 10 * 60 * 1000, // 10 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};
