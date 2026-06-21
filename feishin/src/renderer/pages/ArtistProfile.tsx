import { useParams, useNavigate } from 'react-router';

import { useArtistProfile } from '/@/renderer/api/hooks';
import { AppRoute } from '/@/renderer/router/routes';
import { Button } from '/@/shared/components/button/button';
import { Group } from '/@/shared/components/group/group';
import { Stack } from '/@/shared/components/stack/stack';
import { Text } from '/@/shared/components/text/text';
import { toast } from '/@/shared/components/toast/toast';

const ArtistProfilePage = () => {
    const { artistName } = useParams<{ artistName: string }>();
    const navigate = useNavigate();
    const decodedArtistName = artistName ? decodeURIComponent(artistName) : '';
    
    const { data: artist, isLoading, error } = useArtistProfile(decodedArtistName);

    if (error) {
        toast.error({
            message: 'Failed to load artist profile',
            title: 'Artist Profile',
        });
    }

    if (isLoading) {
        return (
            <Stack gap="md" p="lg">
                <Text fw={700} size="xl">Artist Profile</Text>
                <Stack gap="md">
                    {[1, 2, 3].map((i) => (
                        <Stack
                            key={i}
                            p="md"
                            style={{
                                background: 'var(--theme-colors-surface)',
                                borderRadius: 12,
                                opacity: 0.5,
                            }}
                        >
                            <div style={{ height: '20px', width: '60%', background: 'rgba(255,255,255,0.1)', borderRadius: 4 }} />
                            <div style={{ height: '16px', width: '40%', background: 'rgba(255,255,255,0.1)', borderRadius: 4 }} />
                        </Stack>
                    ))}
                </Stack>
            </Stack>
        );
    }

    if (!artist) {
        return (
            <Stack gap="md" p="lg">
                <Text fw={700} size="xl">Artist Profile</Text>
                <Text variant="secondary">Artist not found</Text>
            </Stack>
        );
    }

    return (
        <Stack gap="md" p="lg">
            <Text fw={700} size="xl">
                {artist.artist_name}
            </Text>
            
            <Stack
                p="md"
                style={{
                    background: 'var(--theme-colors-surface)',
                    borderRadius: 12,
                }}
            >
                <Text fw={600} size="lg">About</Text>
                <Text variant="secondary">
                    {artist.total_songs} songs • {artist.total_plays} total plays • {artist.total_likes} likes
                </Text>
                <Text variant="secondary">
                    Genres: {artist.genres.join(', ')}
                </Text>
                <Group>
                    <Button variant="default">Follow</Button>
                    <Button className="telegram-primary-btn">Donate</Button>
                    <Button variant="outline" onClick={() => navigate(AppRoute.ARTIST_DASHBOARD)}>
                        Artist Dashboard
                    </Button>
                </Group>
            </Stack>

            <Text fw={600} size="lg">Top Songs</Text>
            {artist.top_songs.map((song) => (
                <Stack
                    key={song.song_id}
                    p="md"
                    style={{
                        background: 'var(--theme-colors-surface)',
                        borderRadius: 12,
                    }}
                >
                    <Text fw={600}>{song.title}</Text>
                    <Text variant="secondary">
                        {song.genre} • {song.play_count} plays • {song.like_count} likes
                    </Text>
                    <Group>
                        <Button variant="default">Play</Button>
                        <Button variant="default">Like</Button>
                    </Group>
                </Stack>
            ))}

            <Text fw={600} size="lg" mt="md">Albums</Text>
            {artist.albums.map((album, index) => (
                <Stack
                    key={index}
                    p="md"
                    style={{
                        background: 'var(--theme-colors-surface)',
                        borderRadius: 12,
                    }}
                >
                    <Text fw={600}>{album.name}</Text>
                    <Text variant="secondary">{album.song_count} songs</Text>
                    <Group>
                        <Button variant="default">Play All</Button>
                    </Group>
                </Stack>
            ))}

            <Stack
                p="md"
                mt="md"
                style={{
                    background: 'var(--theme-colors-surface)',
                    borderRadius: 12,
                }}
            >
                <Text fw={600} size="lg">Marketplace</Text>
                <Text variant="secondary">Support this artist by purchasing their content</Text>
                <Group>
                    <Button className="telegram-primary-btn">View in Marketplace</Button>
                </Group>
            </Stack>
        </Stack>
    );
};

export default ArtistProfilePage;
