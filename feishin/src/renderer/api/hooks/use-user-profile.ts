import { useQuery } from '@tanstack/react-query';

import { getUserProfile, type UserProfile } from '../client';
import { getBackendUserId } from '../client';

export const useUserProfile = () => {
    const userId = getBackendUserId();

    return useQuery({
        queryKey: ['user-profile', userId],
        queryFn: async (): Promise<UserProfile> => {
            if (!userId) {
                throw new Error('User not authenticated');
            }
            return await getUserProfile(userId);
        },
        enabled: !!userId,
        staleTime: 10 * 60 * 1000, // 10 minutes
        gcTime: 30 * 60 * 1000, // 30 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};
