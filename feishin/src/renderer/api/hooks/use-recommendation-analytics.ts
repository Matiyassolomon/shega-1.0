import { useQuery } from '@tanstack/react-query';

import {
    getRecommendationAnalytics,
    explainRecommendation,
    type RecommendationAnalytics,
    type RecommendationExplanation,
} from '../client';

export const useRecommendationAnalytics = (userId: string) => {
    return useQuery({
        queryKey: ['recommendation-analytics', userId],
        queryFn: async (): Promise<RecommendationAnalytics> => {
            return await getRecommendationAnalytics(userId);
        },
        enabled: !!userId,
        staleTime: 10 * 60 * 1000, // 10 minutes
        gcTime: 30 * 60 * 1000, // 30 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};

export const useRecommendationExplanation = (userId: string, songId: string) => {
    return useQuery({
        queryKey: ['recommendation-explanation', userId, songId],
        queryFn: async (): Promise<RecommendationExplanation> => {
            return await explainRecommendation(userId, songId);
        },
        enabled: !!userId && !!songId,
        staleTime: 5 * 60 * 1000, // 5 minutes
        gcTime: 10 * 60 * 1000, // 10 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};
