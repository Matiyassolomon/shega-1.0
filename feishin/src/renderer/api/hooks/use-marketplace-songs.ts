import { useQuery } from '@tanstack/react-query';

import { getMarketplaceSongs, type MarketplaceSong } from '../client';

export const useMarketplaceSongs = () => {
    return useQuery({
        queryKey: ['marketplace-songs'],
        queryFn: async (): Promise<MarketplaceSong[]> => {
            return await getMarketplaceSongs();
        },
        staleTime: 3 * 60 * 1000, // 3 minutes
        gcTime: 5 * 60 * 1000, // 5 minutes
        retry: 2,
        refetchOnWindowFocus: false,
    });
};
