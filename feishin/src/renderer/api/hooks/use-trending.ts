import { useQuery } from '@tanstack/react-query';

import { getTrending, type TrendingPayload } from '../client';

export const useTrending = (location?: string) => {
    return useQuery({
        queryKey: ['trending', location],
        queryFn: async (): Promise<TrendingPayload> => {
            return await getTrending(location);
        },
        staleTime: 5 * 60 * 1000, // 5 minutes
        gcTime: 10 * 60 * 1000, // 10 minutes
        retry: 2,
        refetchOnWindowFocus: false,
    });
};
