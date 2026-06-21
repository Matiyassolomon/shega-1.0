import { useQuery } from '@tanstack/react-query';

import { getArtistProfile, type ArtistProfile } from '../client';

export const useArtistProfile = (artistName: string) => {
    return useQuery({
        queryKey: ['artist-profile', artistName],
        queryFn: async (): Promise<ArtistProfile> => {
            return await getArtistProfile(artistName);
        },
        enabled: !!artistName,
        staleTime: 10 * 60 * 1000, // 10 minutes
        gcTime: 30 * 60 * 1000, // 30 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};
