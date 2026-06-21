import { useState } from 'react';
import { useNavigate } from 'react-router';

import {
    useAdminDashboard,
    useAdminUsers,
    useAdminArtists,
    useAdminPayments,
} from '/@/renderer/api/hooks';
import { Button } from '/@/shared/components/button/button';
import { Group } from '/@/shared/components/group/group';
import { Stack } from '/@/shared/components/stack/stack';
import { Text } from '/@/shared/components/text/text';
import { toast } from '/@/shared/components/toast/toast';

type AdminTab = 'overview' | 'users' | 'artists' | 'payments';

const AdminDashboardPage = () => {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState<AdminTab>('overview');
    const [paymentsStatus, setPaymentsStatus] = useState<string | undefined>(undefined);
    
    const dashboard = useAdminDashboard();
    const users = useAdminUsers(20, 0);
    const artists = useAdminArtists(20, 0);
    const payments = useAdminPayments(20, 0, paymentsStatus);

    const formatPrice = (amount: number) => {
        return new Intl.NumberFormat('et-ET', {
            style: 'currency',
            currency: 'ETB',
        }).format(amount);
    };

    const formatNumber = (num: number) => {
        return new Intl.NumberFormat('en-US').format(num);
    };

    return (
        <Stack gap="md" p="lg">
            <Group>
                <Text fw={700} size="xl">Admin Dashboard</Text>
                <Button variant="default" onClick={() => navigate(-1)}>Back</Button>
            </Group>

            {/* Tabs */}
            <Group>
                <Button
                    variant={activeTab === 'overview' ? 'default' : 'outline'}
                    onClick={() => setActiveTab('overview')}
                >
                    Overview
                </Button>
                <Button
                    variant={activeTab === 'users' ? 'default' : 'outline'}
                    onClick={() => setActiveTab('users')}
                >
                    Users
                </Button>
                <Button
                    variant={activeTab === 'artists' ? 'default' : 'outline'}
                    onClick={() => setActiveTab('artists')}
                >
                    Artists
                </Button>
                <Button
                    variant={activeTab === 'payments' ? 'default' : 'outline'}
                    onClick={() => setActiveTab('payments')}
                >
                    Payments
                </Button>
            </Group>

            {/* Overview Tab */}
            {activeTab === 'overview' && (
                <>
                    {dashboard.isLoading ? (
                        <Text variant="secondary">Loading dashboard...</Text>
                    ) : dashboard.data ? (
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                            gap: '16px',
                        }}>
                            <Stack
                                p="md"
                                style={{
                                    background: 'var(--theme-colors-surface)',
                                    borderRadius: 12,
                                    border: '1px solid rgba(255,255,255,0.1)',
                                }}
                            >
                                <Text variant="secondary" size="sm">Total Users</Text>
                                <Text fw={700} size="xl">{formatNumber(dashboard.data.total_users)}</Text>
                            </Stack>
                            <Stack
                                p="md"
                                style={{
                                    background: 'var(--theme-colors-surface)',
                                    borderRadius: 12,
                                    border: '1px solid rgba(255,255,255,0.1)',
                                }}
                            >
                                <Text variant="secondary" size="sm">Total Artists</Text>
                                <Text fw={700} size="xl">{formatNumber(dashboard.data.total_artists)}</Text>
                            </Stack>
                            <Stack
                                p="md"
                                style={{
                                    background: 'var(--theme-colors-surface)',
                                    borderRadius: 12,
                                    border: '1px solid rgba(255,255,255,0.1)',
                                }}
                            >
                                <Text variant="secondary" size="sm">Total Songs</Text>
                                <Text fw={700} size="xl">{formatNumber(dashboard.data.total_songs)}</Text>
                            </Stack>
                            <Stack
                                p="md"
                                style={{
                                    background: 'var(--theme-colors-surface)',
                                    borderRadius: 12,
                                    border: '1px solid rgba(255,255,255,0.1)',
                                }}
                            >
                                <Text variant="secondary" size="sm">Total Plays</Text>
                                <Text fw={700} size="xl">{formatNumber(dashboard.data.total_plays)}</Text>
                            </Stack>
                            <Stack
                                p="md"
                                style={{
                                    background: 'var(--theme-colors-surface)',
                                    borderRadius: 12,
                                    border: '1px solid rgba(255,255,255,0.1)',
                                }}
                            >
                                <Text variant="secondary" size="sm">Total Likes</Text>
                                <Text fw={700} size="xl">{formatNumber(dashboard.data.total_likes)}</Text>
                            </Stack>
                            <Stack
                                p="md"
                                style={{
                                    background: 'var(--theme-colors-surface)',
                                    borderRadius: 12,
                                    border: '1px solid rgba(255,255,255,0.1)',
                                }}
                            >
                                <Text variant="secondary" size="sm">Total Revenue</Text>
                                <Text fw={700} size="xl" style={{ color: 'var(--consumer-accent, #f4c542)' }}>
                                    {formatPrice(dashboard.data.total_revenue)}
                                </Text>
                            </Stack>
                            <Stack
                                p="md"
                                style={{
                                    background: 'var(--theme-colors-surface)',
                                    borderRadius: 12,
                                    border: '1px solid rgba(255,255,255,0.1)',
                                }}
                            >
                                <Text variant="secondary" size="sm">Active Subscriptions</Text>
                                <Text fw={700} size="xl">{formatNumber(dashboard.data.active_subscriptions)}</Text>
                            </Stack>
                            <Stack
                                p="md"
                                style={{
                                    background: 'var(--theme-colors-surface)',
                                    borderRadius: 12,
                                    border: '1px solid rgba(255,255,255,0.1)',
                                }}
                            >
                                <Text variant="secondary" size="sm">Pending Payouts</Text>
                                <Text fw={700} size="xl" style={{ color: '#faad14' }}>
                                    {formatNumber(dashboard.data.pending_payouts)}
                                </Text>
                            </Stack>
                            <Stack
                                p="md"
                                style={{
                                    background: 'var(--theme-colors-surface)',
                                    borderRadius: 12,
                                    border: '1px solid rgba(255,255,255,0.1)',
                                }}
                            >
                                <Text variant="secondary" size="sm">Recent Signups</Text>
                                <Text fw={700} size="xl" style={{ color: '#52c41a' }}>
                                    {formatNumber(dashboard.data.recent_signups)}
                                </Text>
                            </Stack>
                        </div>
                    ) : (
                        <Text variant="secondary">Failed to load dashboard data</Text>
                    )}
                </>
            )}

            {/* Users Tab */}
            {activeTab === 'users' && (
                <>
                    <Text fw={600} size="lg">Users</Text>
                    {users.isLoading ? (
                        <Text variant="secondary">Loading users...</Text>
                    ) : users.data && users.data.users.length > 0 ? (
                        <Stack gap="xs">
                            {users.data.users.map((user) => (
                                <Stack
                                    key={user.id}
                                    p="md"
                                    style={{
                                        background: 'var(--theme-colors-surface)',
                                        borderRadius: 12,
                                        border: '1px solid rgba(255,255,255,0.1)',
                                    }}
                                >
                                    <Group>
                                        <Text fw={600}>{user.username}</Text>
                                        <Text variant="secondary" size="sm">{user.email}</Text>
                                        <Text
                                            size="sm"
                                            style={{
                                                padding: '4px 8px',
                                                borderRadius: '4px',
                                                background: user.subscription_status === 'premium' ? '#52c41a20' : '#8c8c8c20',
                                                color: user.subscription_status === 'premium' ? '#52c41a' : '#8c8c8c',
                                            }}
                                        >
                                            {user.subscription_status}
                                        </Text>
                                        {user.is_active ? (
                                            <Text size="sm" style={{ color: '#52c41a' }}>Active</Text>
                                        ) : (
                                            <Text size="sm" style={{ color: '#ff4d4f' }}>Inactive</Text>
                                        )}
                                    </Group>
                                </Stack>
                            ))}
                        </Stack>
                    ) : (
                        <Text variant="secondary">No users found</Text>
                    )}
                </>
            )}

            {/* Artists Tab */}
            {activeTab === 'artists' && (
                <>
                    <Text fw={600} size="lg">Artists</Text>
                    {artists.isLoading ? (
                        <Text variant="secondary">Loading artists...</Text>
                    ) : artists.data && artists.data.artists.length > 0 ? (
                        <Stack gap="xs">
                            {artists.data.artists.map((artist) => (
                                <Stack
                                    key={artist.id}
                                    p="md"
                                    style={{
                                        background: 'var(--theme-colors-surface)',
                                        borderRadius: 12,
                                        border: '1px solid rgba(255,255,255,0.1)',
                                    }}
                                >
                                    <Group>
                                        <Text fw={600}>{artist.name}</Text>
                                        {artist.verified && (
                                            <Text size="sm" style={{ color: '#1890ff' }}>✓ Verified</Text>
                                        )}
                                        <Text variant="secondary" size="sm">
                                            {artist.song_count} songs
                                        </Text>
                                        <Text variant="secondary" size="sm">
                                            {formatNumber(artist.total_plays)} plays
                                        </Text>
                                        <Text fw={600} style={{ color: 'var(--consumer-accent, #f4c542)' }}>
                                            {formatPrice(artist.total_revenue)}
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

            {/* Payments Tab */}
            {activeTab === 'payments' && (
                <>
                    <Group>
                        <Text fw={600} size="lg">Payments</Text>
                        <Group>
                            <Button
                                variant={paymentsStatus === undefined ? 'default' : 'outline'}
                                size="sm"
                                onClick={() => setPaymentsStatus(undefined)}
                            >
                                All
                            </Button>
                            <Button
                                variant={paymentsStatus === 'completed' ? 'default' : 'outline'}
                                size="sm"
                                onClick={() => setPaymentsStatus('completed')}
                            >
                                Completed
                            </Button>
                            <Button
                                variant={paymentsStatus === 'pending' ? 'default' : 'outline'}
                                size="sm"
                                onClick={() => setPaymentsStatus('pending')}
                            >
                                Pending
                            </Button>
                        </Group>
                    </Group>
                    {payments.isLoading ? (
                        <Text variant="secondary">Loading payments...</Text>
                    ) : payments.data && payments.data.payments.length > 0 ? (
                        <Stack gap="xs">
                            {payments.data.payments.map((payment) => (
                                <Stack
                                    key={payment.id}
                                    p="md"
                                    style={{
                                        background: 'var(--theme-colors-surface)',
                                        borderRadius: 12,
                                        border: '1px solid rgba(255,255,255,0.1)',
                                    }}
                                >
                                    <Group>
                                        <Text fw={600}>{payment.id}</Text>
                                        <Text variant="secondary" size="sm">User {payment.user_id}</Text>
                                        <Text fw={600} style={{ color: 'var(--consumer-accent, #f4c542)' }}>
                                            {formatPrice(payment.amount)}
                                        </Text>
                                        <Text
                                            size="sm"
                                            style={{
                                                padding: '4px 8px',
                                                borderRadius: '4px',
                                                background:
                                                    payment.status === 'completed' ? '#52c41a20' :
                                                    payment.status === 'pending' ? '#faad1420' :
                                                    '#ff4d4f20',
                                                color:
                                                    payment.status === 'completed' ? '#52c41a' :
                                                    payment.status === 'pending' ? '#faad14' :
                                                    '#ff4d4f',
                                            }}
                                        >
                                            {payment.status}
                                        </Text>
                                        <Text variant="secondary" size="sm">{payment.payment_type}</Text>
                                        <Text variant="secondary" size="xs">
                                            {new Date(payment.created_at).toLocaleDateString()}
                                        </Text>
                                    </Group>
                                </Stack>
                            ))}
                        </Stack>
                    ) : (
                        <Text variant="secondary">No payments found</Text>
                    )}
                </>
            )}
        </Stack>
    );
};

export default AdminDashboardPage;
