import { useQuery } from '@tanstack/react-query';

import {
    getRecommendations,
    type RecommendationPayload,
} from '../client';
import { classifyError } from '../errors';
import { getBackendUserId } from '../client';

export const useRecommendations = (location?: string) => {
    const userId = getBackendUserId();

    return useQuery({
        queryKey: ['recommendations', userId, location],
        queryFn: async (): Promise<RecommendationPayload> => {
            if (!userId) {
                throw new Error('User not authenticated');
            }
            return await getRecommendations(userId, location);
        },
        enabled: !!userId,
        staleTime: 5 * 60 * 1000, // 5 minutes
        gcTime: 10 * 60 * 1000, // 10 minutes
        retry: 2,
        refetchOnWindowFocus: false,
    });
};
