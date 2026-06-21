import { useQuery } from '@tanstack/react-query';

import { getMarketplacePlaylists, type MarketplacePlaylist } from '../client';

export const useMarketplacePlaylists = () => {
    return useQuery({
        queryKey: ['marketplace-playlists'],
        queryFn: async (): Promise<MarketplacePlaylist[]> => {
            return await getMarketplacePlaylists();
        },
        staleTime: 3 * 60 * 1000, // 3 minutes
        gcTime: 5 * 60 * 1000, // 5 minutes
        retry: 2,
        refetchOnWindowFocus: false,
    });
};
