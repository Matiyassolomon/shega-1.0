/**
 * Search Hooks Tests
 * Tests for search-related React Query hooks.
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { useSearchAutocomplete, useSearchSongs, useSearchArtists } from '../use-search';

// Mock the API client
jest.mock('/@/renderer/api/client', () => ({
    searchAutocomplete: jest.fn(),
    searchSongs: jest.fn(),
    searchArtists: jest.fn(),
}));

import { searchAutocomplete, searchSongs, searchArtists } from '/@/renderer/api/client';

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
            },
        },
    });
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
};

describe('useSearchAutocomplete', () => {
    it('should fetch autocomplete suggestions', async () => {
        const mockSuggestions = {
            suggestions: [
                { type: 'song', text: 'Test Song', artist: 'Test Artist', relevance: 0.9 },
            ],
        };
        (searchAutocomplete as jest.Mock).mockResolvedValue(mockSuggestions);

        const { result } = renderHook(() => useSearchAutocomplete('test'), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(result.current.data).toEqual(mockSuggestions);
    });

    it('should not fetch with short query', () => {
        const { result } = renderHook(() => useSearchAutocomplete('t'), {
            wrapper: createWrapper(),
        });

        expect(result.current.isFetching).toBe(false);
    });
});

describe('useSearchSongs', () => {
    it('should fetch search results', async () => {
        const mockResults = {
            query: 'test',
            total: 1,
            offset: 0,
            limit: 20,
            sort_by: 'relevance',
            results: [
                {
                    song_id: '1',
                    title: 'Test Song',
                    artist: 'Test Artist',
                    genre: 'Pop',
                    play_count_7d: 100,
                    like_count_7d: 50,
                    cover_art_path: null,
                    relevance_score: 0.9,
                },
            ],
        };
        (searchSongs as jest.Mock).mockResolvedValue(mockResults);

        const { result } = renderHook(() => useSearchSongs('test'), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(result.current.data).toEqual(mockResults);
    });
});

describe('useSearchArtists', () => {
    it('should fetch artist search results', async () => {
        const mockResults = {
            query: 'test',
            results: [
                {
                    artist: 'Test Artist',
                    song_count: 10,
                    total_plays: 1000,
                    relevance_score: 0.9,
                },
            ],
        };
        (searchArtists as jest.Mock).mockResolvedValue(mockResults);

        const { result } = renderHook(() => useSearchArtists('test'), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(result.current.data).toEqual(mockResults);
    });
});
