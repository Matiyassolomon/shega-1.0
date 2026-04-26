// @ts-nocheck
import { createPayment, getBackendUserId } from '/@/renderer/api/client';
import { Button } from '/@/shared/components/button/button';
import { Stack } from '/@/shared/components/stack/stack';
import { Text } from '/@/shared/components/text/text';
import { toast } from '/@/shared/components/toast/toast';

const PaymentsPage = () => {
    const userId = getBackendUserId();

    const handlePayment = async (
        type: 'playlist_purchase' | 'song_purchase' | 'subscription_monthly' | 'wallet_topup',
    ) => {
        try {
            const amount = type === 'subscription_monthly' ? 199 : type === 'song_purchase' ? 25 : 50;
            const result = await createPayment({
                amount,
                method: 'telebirr',
                payment_type: type, // Aligned with backend 'payment_type' field
                user_id: userId,
            });

            // Support for H5/Web redirect flows (Telebirr Official/Chapa)
            if (result.redirect_url) {
                window.open(result.redirect_url, '_blank');
            }

            toast.success({
                message: `Payment ${result.payment_id || result.id} created with status ${result.status}.`,
                title: 'Payments',
            });
        } catch (error: any) {
            toast.error({ message: error?.message || 'payment failed', title: 'Payments' });
        }
    };

    return (
        <Stack gap="md" p="lg">
            <Text fw={700} size="xl">
                Payments
            </Text>
            <Stack className="telegram-panel" gap="sm" p="md">
                <Text fw={600}>Subscription</Text>
                <Text size="sm" variant="secondary">
                    Unlimited premium tracks for one month.
                </Text>
                <Button
                    className="telegram-primary-btn"
                    onClick={() => handlePayment('subscription_monthly')}
                >
                    Subscribe monthly
                </Button>
            </Stack>
            <Stack className="telegram-panel" gap="sm" p="md">
                <Text fw={600}>Wallet</Text>
                <Text size="sm" variant="secondary">
                    Add balance to buy songs, playlists, and premium content.
                </Text>
                <Button onClick={() => handlePayment('wallet_topup')}>Top-up wallet</Button>
            </Stack>
            <Stack className="telegram-panel" gap="sm" p="md">
                <Text fw={600}>Playlist Purchase</Text>
                <Text size="sm" variant="secondary">
                    Buy curated Ethiopian playlists from creators.
                </Text>
                <Button onClick={() => handlePayment('playlist_purchase')}>
                    Purchase playlist
                </Button>
            </Stack>
            <Stack className="telegram-panel" gap="sm" p="md">
                <Text fw={600}>Song Purchase</Text>
                <Text size="sm" variant="secondary">
                    Buy individual songs from the marketplace when you do not want the full playlist.
                </Text>
                <Button onClick={() => handlePayment('song_purchase')}>Purchase song</Button>
            </Stack>
        </Stack>
    );
};

export default PaymentsPage;
