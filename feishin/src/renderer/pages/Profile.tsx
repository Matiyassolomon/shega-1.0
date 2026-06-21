import { useUserProfile } from '/@/renderer/api/hooks';
import { useBackendAuth } from '/@/renderer/hooks/use-backend-auth';
import { Stack } from '/@/shared/components/stack/stack';
import { Text } from '/@/shared/components/text/text';
import { toast } from '/@/shared/components/toast/toast';

const ProfilePage = () => {
    const { userId } = useBackendAuth();
    const { data: profile, isLoading, error } = useUserProfile();

    if (error) {
        toast.error({
            message: 'Failed to load profile',
            title: 'Profile',
        });
    }

    return (
        <Stack gap="md" p="lg">
            <Text fw={700} size="xl">
                Profile
            </Text>
            <Text variant="secondary">User ID: {userId || 'Not authenticated'}</Text>
            {isLoading ? (
                <Text variant="secondary">Loading profile...</Text>
            ) : profile ? (
                <Stack className="telegram-panel" gap="xs" p="md">
                    <Text>Device class: {profile.device_class}</Text>
                    <Text>
                        Subscription: {profile.subscription_status}
                        {profile.expires_at ? ` until ${profile.expires_at}` : ''}
                    </Text>
                    <Text>Recent playback events: {profile.recent_playback_count}</Text>
                    <Text>
                        Preferred location: {profile.preferred_location || 'Not learned yet'}
                    </Text>
                    <Text>
                        Secure playlists: {profile.secure_playlist_ids.length > 0 ? profile.secure_playlist_ids.join(', ') : 'None yet'}
                    </Text>
                    <Text>
                        Top lookalikes:{' '}
                        {profile.lookalike_audience.length > 0
                            ? profile.lookalike_audience
                                  .map(
                                      (item) =>
                                          `#${item.user_id} (${Math.round(item.similarity * 100)}%)`,
                                  )
                                  .join(', ')
                            : 'No matches yet'}
                    </Text>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        {JSON.stringify(profile.taste_vector, null, 2)}
                    </pre>
                </Stack>
            ) : (
                <Text variant="secondary">No profile data available</Text>
            )}
        </Stack>
    );
};

export default ProfilePage;
