// @ts-nocheck
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import {
    createPayment,
    confirmPayment,
    checkSubscription,
    getPaymentProviders,
    handleApiError,
    type LegacyPayment,
    getBackendUserId,
} from '/@/renderer/api/aligned-client';
import { Stack } from '/@/shared/components/stack/stack';
import { Text } from '/@/shared/components/text/text';
import { toast } from '/@/shared/components/toast/toast';
import { AppRoute } from '/@/renderer/router/routes';
import { 
    ResponsiveLayout, 
    ResponsiveGrid, 
    ResponsiveCard, 
    ResponsiveButton 
} from '/@/renderer/components/ResponsiveLayout';

const AlignedPaymentsPage = () => {
    const userId = getBackendUserId();
    const [loading, setLoading] = useState(false);
    const [subscriptionStatus, setSubscriptionStatus] = useState<{ subscribed: boolean } | null>(null);
    const [currentPayment, setCurrentPayment] = useState<LegacyPayment | null>(null);
    const [selectedProvider, setSelectedProvider] = useState('telebirr');

    const paymentProviders = getPaymentProviders();

    useEffect(() => {
        loadSubscriptionStatus();
    }, [userId]);

    const loadSubscriptionStatus = async () => {
        try {
            const status = await checkSubscription(userId);
            setSubscriptionStatus(status);
        } catch (error) {
            console.error('Failed to load subscription status:', error);
        }
    };

    const handlePayment = async (
        type: 'playlist_purchase' | 'song_purchase' | 'subscription_monthly' | 'wallet_topup',
    ) => {
        setLoading(true);
        try {
            const amount = type === 'subscription_monthly' ? 199 : type === 'song_purchase' ? 25 : 50;
            
            // Step 1: Create payment
            const payment = await createPayment({
                amount,
                method: selectedProvider as 'telebirr' | 'cbe',
                user_id: userId,
                payment_type: type,
            });

            setCurrentPayment(payment);
            
            toast.success({
                message: `Payment ${payment.id} created with status ${payment.status}.`,
                title: 'Payment Created',
            });

            // Step 2: For demo purposes, auto-confirm after 2 seconds
            // In real implementation, this would happen after actual payment
            setTimeout(async () => {
                try {
                    const result = await confirmPayment({
                        payment_id: payment.id,
                    });

                    toast.success({
                        message: `Payment confirmed! Status: ${result.status}`,
                        title: 'Payment Complete',
                    });

                    // Reload subscription status
                    await loadSubscriptionStatus();
                    setCurrentPayment(null);
                } catch (error) {
                    toast.error({
                        message: 'Payment confirmation failed',
                        title: 'Confirmation Error',
                    });
                }
            }, 2000);

        } catch (error: any) {
            const apiError = handleApiError(error);
            toast.error({ 
                message: apiError.message, 
                title: 'Payment Failed' 
            });
        } finally {
            setLoading(false);
        }
    };

    const formatPrice = (amount: number) => {
        return new Intl.NumberFormat('et-ET', {
            style: 'currency',
            currency: 'ETB',
        }).format(amount);
    };

    return (
        <ResponsiveLayout title="💳 Payments" showBackButton onBackClick={() => navigate(AppRoute.HOME)}>
            <Stack spacing="xl">
                {/* Current Subscription Status */}
                {subscriptionStatus && (
                    <ResponsiveCard title="Subscription Status">
                        {subscriptionStatus.subscribed ? (
                            <Stack spacing="md">
                                <div style={{ color: '#52c41a', fontWeight: 'bold' }}>
                                    ✅ Active Subscription
                                </div>
                                <Text size="sm" style={{ color: '#6b7280' }}>
                                    You have access to premium features
                                </Text>
                            </Stack>
                        ) : (
                            <Stack spacing="md">
                                <div style={{ color: '#ff4d4f', fontWeight: 'bold' }}>
                                    ❌ No Active Subscription
                                </div>
                                <Text size="sm" style={{ color: '#6b7280' }}>
                                    Subscribe to unlock premium features
                                </Text>
                            </Stack>
                        )}
                    </ResponsiveCard>
                )}

                {/* Payment Provider Selection */}
                <ResponsiveCard title="Select Payment Method">
                    <Stack spacing="md">
                        <Text size="sm" style={{ color: '#6b7280' }}>
                            Choose your preferred payment provider
                        </Text>
                        <ResponsiveGrid columns={{ mobile: 1, tablet: 2, desktop: 2 }}>
                            {paymentProviders.map((provider) => (
                                <ResponsiveButton
                                    key={provider.id}
                                    onClick={() => setSelectedProvider(provider.id)}
                                    variant={selectedProvider === provider.id ? 'primary' : 'secondary'}
                                    fullWidth
                                >
                                    <Stack spacing="xs" align="center">
                                        <Text weight="bold">{provider.name}</Text>
                                        <Text size="xs" style={{ opacity: 0.8 }}>
                                            {provider.description}
                                        </Text>
                                        {provider.status === 'recommended' && (
                                            <div style={{ 
                                                backgroundColor: '#1DB954', 
                                                color: 'white', 
                                                padding: '2px 8px', 
                                                borderRadius: '12px', 
                                                fontSize: '10px',
                                                fontWeight: 'bold'
                                            }}>
                                                RECOMMENDED
                                            </div>
                                        )}
                                    </Stack>
                                </ResponsiveButton>
                            ))}
                        </ResponsiveGrid>
                    </Stack>
                </ResponsiveCard>

                {/* Payment Options */}
                <ResponsiveGrid columns={{ mobile: 1, tablet: 2, desktop: 3 }}>
                    <ResponsiveCard title="Premium Subscription" subtitle="Unlimited access">
                        <Stack spacing="md">
                            <div style={{ fontSize: '32px', textAlign: 'center' }}>🎵</div>
                            <Text size="sm" style={{ textAlign: 'center', color: '#6b7280' }}>
                                Unlimited premium tracks for one month
                            </Text>
                            <ResponsiveButton 
                                onClick={() => handlePayment('subscription_monthly')}
                                disabled={loading || subscriptionStatus?.subscribed}
                                fullWidth
                                variant="primary"
                            >
                                {loading ? 'Processing...' : `Subscribe - ${formatPrice(199)}`}
                            </ResponsiveButton>
                        </Stack>
                    </ResponsiveCard>

                    <ResponsiveCard title="Wallet Top-up" subtitle="Add funds">
                        <Stack spacing="md">
                            <div style={{ fontSize: '32px', textAlign: 'center' }}>💰</div>
                            <Text size="sm" style={{ textAlign: 'center', color: '#6b7280' }}>
                                Add funds to your wallet for purchases
                            </Text>
                            <ResponsiveButton 
                                onClick={() => handlePayment('wallet_topup')}
                                disabled={loading}
                                fullWidth
                                variant="secondary"
                            >
                                {loading ? 'Processing...' : `Top-up - ${formatPrice(50)}`}
                            </ResponsiveButton>
                        </Stack>
                    </ResponsiveCard>

                    <ResponsiveCard title="Purchase Song" subtitle="Individual tracks">
                        <Stack spacing="md">
                            <div style={{ fontSize: '32px', textAlign: 'center' }}>🎧</div>
                            <Text size="sm" style={{ textAlign: 'center', color: '#6b7280' }}>
                                Buy individual songs for permanent access
                            </Text>
                            <ResponsiveButton 
                                onClick={() => handlePayment('song_purchase')}
                                disabled={loading}
                                fullWidth
                                variant="outline"
                            >
                                {loading ? 'Processing...' : `Buy Song - ${formatPrice(25)}`}
                            </ResponsiveButton>
                        </Stack>
                    </ResponsiveCard>
                </ResponsiveGrid>
                {/* Current Payment Status */}
                {currentPayment && (
                    <ResponsiveCard title="Payment Processing">
                        <Stack spacing="md">
                            <Text size="sm" style={{ color: '#6b7280' }}>
                                Payment ID: {currentPayment.payment_id}
                            </Text>
                            <Text size="sm" style={{ color: '#6b7280' }}>
                                Status: {currentPayment.status}
                            </Text>
                            <Text size="sm" style={{ color: '#6b7280' }}>
                                Provider: {selectedProvider}
                            </Text>
                            <Text size="sm" style={{ color: '#1DB954', fontStyle: 'italic' }}>
                                This is a demo - payment will be confirmed automatically
                            </Text>
                            {currentPayment.redirect_url && (
                                <ResponsiveButton 
                                    onClick={() => window.open(currentPayment.redirect_url, '_blank')}
                                    variant="primary"
                                    fullWidth
                                >
                                    Complete Payment
                                </ResponsiveButton>
                            )}
                        </Stack>
                    </ResponsiveCard>
                )}

                {/* Features */}
                <ResponsiveCard title="Premium Features">
                    <ResponsiveGrid columns={{ mobile: 1, tablet: 2, desktop: 3 }}>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '20px', marginBottom: '8px' }}> Unlimited premium tracks</div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '20px', marginBottom: '8px' }}> High-quality audio</div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '20px', marginBottom: '8px' }}> Offline downloads</div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '20px', marginBottom: '8px' }}> No advertisements</div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '20px', marginBottom: '8px' }}> Advanced search</div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '20px', marginBottom: '8px' }}> Exclusive content</div>
                        </div>
                    </ResponsiveGrid>
                </ResponsiveCard>
            </Stack>
        </ResponsiveLayout>
    );
};

export default AlignedPaymentsPage;
