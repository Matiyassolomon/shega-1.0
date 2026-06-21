import { useQuery } from '@tanstack/react-query';

import {
    searchAutocomplete,
    searchSongs,
    searchArtists,
    type SearchAutocompleteResponse,
    type SearchResponse,
    type ArtistSearchResponse,
} from '../client';

export const useSearchAutocomplete = (query: string, enabled: boolean = true) => {
    return useQuery({
        queryKey: ['search-autocomplete', query],
        queryFn: async (): Promise<SearchAutocompleteResponse> => {
            return await searchAutocomplete(query);
        },
        enabled: enabled && query.length >= 2,
        staleTime: 5 * 60 * 1000, // 5 minutes
        gcTime: 10 * 60 * 1000, // 10 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};

export const useSearchSongs = (
    query: string,
    limit: number = 20,
    offset: number = 0,
    sortBy: 'relevance' | 'popularity' | 'recent' = 'relevance',
) => {
    return useQuery({
        queryKey: ['search-songs', query, limit, offset, sortBy],
        queryFn: async (): Promise<SearchResponse> => {
            return await searchSongs(query, limit, offset, sortBy);
        },
        enabled: query.length >= 1,
        staleTime: 2 * 60 * 1000, // 2 minutes
        gcTime: 5 * 60 * 1000, // 5 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};

export const useSearchArtists = (query: string, limit: number = 20) => {
    return useQuery({
        queryKey: ['search-artists', query, limit],
        queryFn: async (): Promise<ArtistSearchResponse> => {
            return await searchArtists(query, limit);
        },
        enabled: query.length >= 1,
        staleTime: 5 * 60 * 1000, // 5 minutes
        gcTime: 10 * 60 * 1000, // 10 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};
