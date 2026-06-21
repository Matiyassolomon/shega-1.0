import { useState } from 'react';
import { useNavigate } from 'react-router';

import {
    useSearchAutocomplete,
    useSearchSongs,
    useSearchArtists,
} from '/@/renderer/api/hooks';
import { Button } from '/@/shared/components/button/button';
import { Group } from '/@/shared/components/group/group';
import { Stack } from '/@/shared/components/stack/stack';
import { Text } from '/@/shared/components/text/text';
import { toast } from '/@/shared/components/toast/toast';

const SearchPage = () => {
    const navigate = useNavigate();
    const [query, setQuery] = useState('');
    const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(null);
    const [sortBy, setSortBy] = useState<'relevance' | 'popularity' | 'recent'>('relevance');
    
    const autocomplete = useSearchAutocomplete(query, query.length >= 2);
    const songs = useSearchSongs(selectedSuggestion || query, 20, 0, sortBy);
    const artists = useSearchArtists(selectedSuggestion || query, 10);

    const handleSearch = (searchQuery: string) => {
        setQuery(searchQuery);
        setSelectedSuggestion(searchQuery);
    };

    const handleSuggestionClick = (suggestion: string) => {
        setQuery(suggestion);
        setSelectedSuggestion(suggestion);
    };

    const handleSortChange = (newSortBy: 'relevance' | 'popularity' | 'recent') => {
        setSortBy(newSortBy);
    };

    const handleSongClick = (songId: string) => {
        // Navigate to song details or play the song
        toast.success({ message: 'Playing song...', title: 'Search' });
    };

    const handleArtistClick = (artist: string) => {
        navigate(`/artist/${encodeURIComponent(artist)}`);
    };

    return (
        <Stack gap="md" p="lg">
            <Text fw={700} size="xl">Search</Text>
            
            {/* Search Input */}
            <div style={{ position: 'relative' }}>
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                            handleSearch(query);
                        }
                    }}
                    placeholder="Search for songs, artists..."
                    style={{
                        width: '100%',
                        padding: '12px 16px',
                        background: 'var(--theme-colors-surface)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: 8,
                        color: 'white',
                        fontSize: '16px',
                    }}
                />
                
                {/* Autocomplete Dropdown */}
                {autocomplete.data && autocomplete.data.suggestions.length > 0 && query.length >= 2 && (
                    <div
                        style={{
                            position: 'absolute',
                            top: '100%',
                            left: 0,
                            right: 0,
                            background: 'var(--theme-colors-background, #121212)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: 8,
                            marginTop: '4px',
                            maxHeight: '300px',
                            overflowY: 'auto',
                            zIndex: 1000,
                        }}
                    >
                        {autocomplete.data.suggestions.map((suggestion, index) => (
                            <div
                                key={index}
                                onClick={() => handleSuggestionClick(suggestion.text)}
                                style={{
                                    padding: '12px 16px',
                                    cursor: 'pointer',
                                    borderBottom: '1px solid rgba(255,255,255,0.05)',
                                    transition: 'background 0.2s',
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.background = 'transparent';
                                }}
                            >
                                <Group>
                                    <Text size="sm">{suggestion.text}</Text>
                                    {suggestion.type === 'song' && suggestion.artist && (
                                        <Text variant="secondary" size="xs">
                                            by {suggestion.artist}
                                        </Text>
                                    )}
                                    <Text variant="secondary" size="xs">
                                        {Math.round(suggestion.relevance * 100)}% match
                                    </Text>
                                </Group>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Sort Options */}
            {selectedSuggestion && (
                <Group>
                    <Text variant="secondary" size="sm">Sort by:</Text>
                    <Button
                        variant={sortBy === 'relevance' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => handleSortChange('relevance')}
                    >
                        Relevance
                    </Button>
                    <Button
                        variant={sortBy === 'popularity' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => handleSortChange('popularity')}
                    >
                        Popularity
                    </Button>
                    <Button
                        variant={sortBy === 'recent' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => handleSortChange('recent')}
                    >
                        Recent
                    </Button>
                </Group>
            )}

            {/* Search Results */}
            {selectedSuggestion && (
                <>
                    {/* Songs */}
                    <Text fw={600} size="lg">Songs</Text>
                    {songs.isLoading ? (
                        <Text variant="secondary">Loading...</Text>
                    ) : songs.data && songs.data.results.length > 0 ? (
                        <Stack gap="xs">
                            {songs.data.results.map((song) => (
                                <Stack
                                    key={song.song_id}
                                    p="md"
                                    style={{
                                        background: 'var(--theme-colors-surface)',
                                        borderRadius: 12,
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        cursor: 'pointer',
                                        transition: 'transform 0.2s',
                                    }}
                                    onClick={() => handleSongClick(song.song_id)}
                                    onMouseEnter={(e) => {
                                        e.currentTarget.style.transform = 'translateY(-2px)';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.currentTarget.style.transform = 'translateY(0)';
                                    }}
                                >
                                    <Group>
                                        <div
                                            style={{
                                                width: '48px',
                                                height: '48px',
                                                background: 'var(--consumer-accent, #f4c542)',
                                                borderRadius: 8,
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                            }}
                                        >
                                            🎵
                                        </div>
                                        <Stack style={{ flex: 1 }}>
                                            <Text fw={600}>{song.title}</Text>
                                            <Text variant="secondary" size="sm">{song.artist}</Text>
                                        </Stack>
                                        <Text variant="secondary" size="xs">
                                            {song.play_count_7d} plays
                                        </Text>
                                        <Text variant="secondary" size="xs">
                                            {Math.round(song.relevance_score * 100)}%
                                        </Text>
                                    </Group>
                                </Stack>
                            ))}
                        </Stack>
                    ) : (
                        <Text variant="secondary">No songs found</Text>
                    )}

                    {/* Artists */}
                    <Text fw={600} size="lg">Artists</Text>
                    {artists.isLoading ? (
                        <Text variant="secondary">Loading...</Text>
                    ) : artists.data && artists.data.results.length > 0 ? (
                        <Stack gap="xs">
                            {artists.data.results.map((result) => (
                                <Stack
                                    key={result.artist}
                                    p="md"
                                    style={{
                                        background: 'var(--theme-colors-surface)',
                                        borderRadius: 12,
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        cursor: 'pointer',
                                        transition: 'transform 0.2s',
                                    }}
                                    onClick={() => handleArtistClick(result.artist)}
                                    onMouseEnter={(e) => {
                                        e.currentTarget.style.transform = 'translateY(-2px)';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.currentTarget.style.transform = 'translateY(0)';
                                    }}
                                >
                                    <Group>
                                        <div
                                            style={{
                                                width: '48px',
                                                height: '48px',
                                                background: 'var(--consumer-accent, #f4c542)',
                                                borderRadius: 8,
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                            }}
                                        >
                                            👨‍🎤
                                        </div>
                                        <Stack style={{ flex: 1 }}>
                                            <Text fw={600}>{result.artist}</Text>
                                            <Text variant="secondary" size="sm">
                                                {result.song_count} songs • {result.total_plays} plays
                                            </Text>
                                        </Stack>
                                        <Text variant="secondary" size="xs">
                                            {Math.round(result.relevance_score * 100)}%
                                        </Text>
                                    </Group>
                                </Stack>
                            ))}
                        </Stack>
                    ) : (
                        <Text variant="secondary">No artists found</Text>
                    )}
                </>
            )}

            {!selectedSuggestion && (
                <Text variant="secondary">Enter a search query to find songs and artists</Text>
            )}
        </Stack>
    );
};

export default SearchPage;
