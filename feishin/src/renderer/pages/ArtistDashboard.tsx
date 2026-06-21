import { useState } from 'react';
import { useNavigate } from 'react-router';

import {
    useArtistDashboard,
    useWallet,
    usePayoutRequests,
    useCreatePayoutRequest,
    useAdRevenue,
} from '/@/renderer/api/hooks';
import { getBackendUserId } from '/@/renderer/api/client';
import { Button } from '/@/shared/components/button/button';
import { Group } from '/@/shared/components/group/group';
import { Stack } from '/@/shared/components/stack/stack';
import { Text } from '/@/shared/components/text/text';
import { toast } from '/@/shared/components/toast/toast';

const ArtistDashboardPage = () => {
    const navigate = useNavigate();
    const userId = getBackendUserId();
    const [payoutModalOpen, setPayoutModalOpen] = useState(false);
    const [payoutAmount, setPayoutAmount] = useState('');
    const [bankAccount, setBankAccount] = useState('');
    const [bankName, setBankName] = useState('');
    
    const dashboard = useArtistDashboard(userId || '');
    const wallet = useWallet(userId || '');
    const payoutRequests = usePayoutRequests(userId || '');
    const adRevenue = useAdRevenue(userId || '');
    const createPayoutMutation = useCreatePayoutRequest(userId || '');

    const handlePayoutSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!userId) return;

        const amount = parseFloat(payoutAmount);
        if (isNaN(amount) || amount <= 0) {
            toast.error({ message: 'Please enter a valid amount', title: 'Payout' });
            return;
        }

        if (!bankAccount || !bankName) {
            toast.error({ message: 'Please fill in all bank details', title: 'Payout' });
            return;
        }

        if (amount > (wallet.data?.balance || 0)) {
            toast.error({ message: 'Insufficient wallet balance', title: 'Payout' });
            return;
        }

        try {
            await createPayoutMutation.mutateAsync({
                amount,
                bank_account: bankAccount,
                bank_name: bankName,
            });
            toast.success({ message: 'Payout request submitted successfully', title: 'Payout' });
            setPayoutModalOpen(false);
            setPayoutAmount('');
            setBankAccount('');
            setBankName('');
        } catch (error: any) {
            toast.error({ message: error?.message || 'Failed to submit payout request', title: 'Payout' });
        }
    };

    const formatPrice = (amount: number) => {
        return new Intl.NumberFormat('et-ET', {
            style: 'currency',
            currency: 'ETB',
        }).format(amount);
    };

    if (!userId) {
        return (
            <Stack gap="md" p="lg">
                <Text fw={700} size="xl">Artist Dashboard</Text>
                <Text variant="secondary">Please log in to access your dashboard</Text>
            </Stack>
        );
    }

    return (
        <Stack gap="md" p="lg">
            <Group>
                <Text fw={700} size="xl">Artist Dashboard</Text>
                <Button variant="default" onClick={() => navigate(-1)}>Back</Button>
            </Group>

            {/* Dashboard Stats */}
            {dashboard.isLoading ? (
                <Stack gap="md">
                    {[1, 2, 3, 4, 5].map((i) => (
                        <div
                            key={i}
                            style={{
                                height: '80px',
                                background: 'var(--theme-colors-surface)',
                                borderRadius: 12,
                                opacity: 0.5,
                            }}
                        />
                    ))}
                </Stack>
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
                        <Text variant="secondary" size="sm">Total Earnings</Text>
                        <Text fw={700} size="xl" style={{ color: 'var(--consumer-accent, #f4c542)' }}>
                            {formatPrice(dashboard.data.total_earnings)}
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
                        <Text variant="secondary" size="sm">Total Plays</Text>
                        <Text fw={700} size="xl">{dashboard.data.total_plays}</Text>
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
                        <Text fw={700} size="xl">{dashboard.data.total_likes}</Text>
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
                        <Text fw={700} size="xl">{dashboard.data.total_songs}</Text>
                    </Stack>
                    {adRevenue.data && (
                        <Stack
                            p="md"
                            style={{
                                background: 'var(--theme-colors-surface)',
                                borderRadius: 12,
                                border: '1px solid rgba(255,255,255,0.1)',
                            }}
                        >
                            <Text variant="secondary" size="sm">Ad Revenue</Text>
                            <Text fw={700} size="xl" style={{ color: '#52c41a' }}>
                                {formatPrice(adRevenue.data.total_revenue)}
                            </Text>
                            <Text variant="secondary" size="xs">
                                {adRevenue.data.total_impressions} impressions
                            </Text>
                        </Stack>
                    )}
                </div>
            ) : (
                <Text variant="secondary">Failed to load dashboard data</Text>
            )}

            {/* Wallet Section */}
            <Text fw={600} size="lg">Wallet</Text>
            {wallet.isLoading ? (
                <div style={{
                    height: '120px',
                    background: 'var(--theme-colors-surface)',
                    borderRadius: 12,
                    opacity: 0.5,
                }}
                />
            ) : wallet.data ? (
                <Stack
                    p="md"
                    style={{
                        background: 'var(--theme-colors-surface)',
                        borderRadius: 12,
                        border: '1px solid rgba(255,255,255,0.1)',
                    }}
                    gap="md"
                >
                    <Group>
                        <Text variant="secondary">Balance</Text>
                        <Text fw={700} size="xl" style={{ color: 'var(--consumer-accent, #f4c542)' }}>
                            {formatPrice(wallet.data.balance)}
                        </Text>
                    </Group>
                    <Button
                        className="telegram-primary-btn"
                        onClick={() => setPayoutModalOpen(true)}
                        disabled={wallet.data.balance <= 0}
                    >
                        Request Payout
                    </Button>
                    {wallet.data.transactions.length === 0 ? (
                        <Text variant="secondary" size="sm">No transactions yet</Text>
                    ) : (
                        <Stack gap="xs">
                            <Text variant="secondary" size="sm">Recent Transactions</Text>
                            {wallet.data.transactions.slice(0, 5).map((tx) => (
                                <Group key={tx.id}>
                                    <Text size="sm">{tx.description}</Text>
                                    <Text
                                        size="sm"
                                        fw={600}
                                        style={{ color: tx.type === 'credit' ? '#52c41a' : '#ff4d4f' }}
                                    >
                                        {tx.type === 'credit' ? '+' : '-'}{formatPrice(tx.amount)}
                                    </Text>
                                </Group>
                            ))}
                        </Stack>
                    )}
                </Stack>
            ) : (
                <Text variant="secondary">Failed to load wallet data</Text>
            )}

            {/* Payout Requests */}
            <Text fw={600} size="lg">Payout Requests</Text>
            {payoutRequests.isLoading ? (
                <div style={{
                    height: '120px',
                    background: 'var(--theme-colors-surface)',
                    borderRadius: 12,
                    opacity: 0.5,
                }}
                />
            ) : payoutRequests.data && payoutRequests.data.length > 0 ? (
                <Stack gap="xs">
                    {payoutRequests.data.map((request) => (
                        <Stack
                            key={request.id}
                            p="md"
                            style={{
                                background: 'var(--theme-colors-surface)',
                                borderRadius: 12,
                                border: '1px solid rgba(255,255,255,0.1)',
                            }}
                        >
                            <Group>
                                <Text fw={600}>{formatPrice(request.amount)}</Text>
                                <Text
                                    size="sm"
                                    style={{
                                        padding: '4px 8px',
                                        borderRadius: '4px',
                                        background:
                                            request.status === 'completed' ? '#52c41a20' :
                                            request.status === 'pending' ? '#faad1420' :
                                            request.status === 'approved' ? '#1890ff20' :
                                            '#ff4d4f20',
                                        color:
                                            request.status === 'completed' ? '#52c41a' :
                                            request.status === 'pending' ? '#faad14' :
                                            request.status === 'approved' ? '#1890ff' :
                                            '#ff4d4f',
                                    }}
                                >
                                    {request.status.toUpperCase()}
                                </Text>
                            </Group>
                            <Text variant="secondary" size="sm">
                                {request.bank_name} - {request.bank_account}
                            </Text>
                            <Text variant="secondary" size="sm">
                                {new Date(request.created_at).toLocaleDateString()}
                            </Text>
                        </Stack>
                    ))}
                </Stack>
            ) : (
                <Text variant="secondary">No payout requests yet</Text>
            )}

            {/* Payout Modal */}
            {payoutModalOpen && (
                <div
                    style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'rgba(0,0,0,0.8)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 1000,
                        padding: '20px',
                    }}
                    onClick={() => setPayoutModalOpen(false)}
                >
                    <div
                        style={{
                            background: 'var(--theme-colors-background, #121212)',
                            borderRadius: 20,
                            padding: '24px',
                            maxWidth: 400,
                            width: '100%',
                            border: '1px solid rgba(255,255,255,0.1)',
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <Stack gap="md">
                            <Text fw={700} size="xl">Request Payout</Text>
                            <form onSubmit={handlePayoutSubmit}>
                                <Stack gap="md">
                                    <div>
                                        <Text variant="secondary" size="sm">Amount (ETB)</Text>
                                        <input
                                            type="number"
                                            value={payoutAmount}
                                            onChange={(e) => setPayoutAmount(e.target.value)}
                                            placeholder="Enter amount"
                                            style={{
                                                width: '100%',
                                                padding: '12px',
                                                background: 'var(--theme-colors-surface)',
                                                border: '1px solid rgba(255,255,255,0.1)',
                                                borderRadius: 8,
                                                color: 'white',
                                            }}
                                        />
                                        <Text variant="secondary" size="sm">
                                            Available: {formatPrice(wallet.data?.balance || 0)}
                                        </Text>
                                    </div>
                                    <div>
                                        <Text variant="secondary" size="sm">Bank Account Number</Text>
                                        <input
                                            type="text"
                                            value={bankAccount}
                                            onChange={(e) => setBankAccount(e.target.value)}
                                            placeholder="Enter account number"
                                            style={{
                                                width: '100%',
                                                padding: '12px',
                                                background: 'var(--theme-colors-surface)',
                                                border: '1px solid rgba(255,255,255,0.1)',
                                                borderRadius: 8,
                                                color: 'white',
                                            }}
                                        />
                                    </div>
                                    <div>
                                        <Text variant="secondary" size="sm">Bank Name</Text>
                                        <input
                                            type="text"
                                            value={bankName}
                                            onChange={(e) => setBankName(e.target.value)}
                                            placeholder="Enter bank name"
                                            style={{
                                                width: '100%',
                                                padding: '12px',
                                                background: 'var(--theme-colors-surface)',
                                                border: '1px solid rgba(255,255,255,0.1)',
                                                borderRadius: 8,
                                                color: 'white',
                                            }}
                                        />
                                    </div>
                                    <Group>
                                        <Button
                                            type="button"
                                            variant="default"
                                            onClick={() => setPayoutModalOpen(false)}
                                            style={{ flex: 1 }}
                                        >
                                            Cancel
                                        </Button>
                                        <Button
                                            type="submit"
                                            className="telegram-primary-btn"
                                            disabled={createPayoutMutation.isPending}
                                            style={{ flex: 1 }}
                                        >
                                            {createPayoutMutation.isPending ? 'Submitting...' : 'Submit'}
                                        </Button>
                                    </Group>
                                </Stack>
                            </form>
                        </Stack>
                    </div>
                </div>
            )}
        </Stack>
    );
};

export default ArtistDashboardPage;
