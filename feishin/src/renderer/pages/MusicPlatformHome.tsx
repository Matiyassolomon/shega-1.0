// @ts-nocheck
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import {
    checkSubscription,
    getPaymentProviders,
    getBackendUserId,
    handleApiError,
    backendClient,
} from '/@/renderer/api/aligned-client';
import { Stack } from '/@/shared/components/stack/stack';
import { Text } from '/@/shared/components/text/text';
import { toast } from '/@/shared/components/toast/toast';
import { AppRoute } from '/@/renderer/router/routes';
import BackendErrorPage from '/@/renderer/pages/BackendErrorPage';
import { 
    ResponsiveLayout, 
    ResponsiveGrid, 
    ResponsiveCard, 
    ResponsiveButton 
} from '/@/renderer/components/ResponsiveLayout';

const MusicPlatformHome = () => {
    const navigate = useNavigate();
    const userId = getBackendUserId();
    const [loading, setLoading] = useState(false);
    const [subscriptionStatus, setSubscriptionStatus] = useState<{ subscribed: boolean } | null>(null);
    const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');

    const paymentProviders = getPaymentProviders();

    useEffect(() => {
        checkBackendConnection();
        loadSubscriptionStatus();
    }, [userId]);

    const checkBackendConnection = async () => {
        try {
            // Try to hit the health endpoint to test backend connection
            await backendClient.get('/health');
            setBackendStatus('online');
        } catch (error) {
            console.error('Backend connection failed:', error);
            setBackendStatus('offline');
        }
    };

    const loadSubscriptionStatus = async () => {
        try {
            const status = await checkSubscription(userId);
            setSubscriptionStatus(status);
        } catch (error) {
            console.error('Failed to load subscription status:', error);
            // Don't show error toast on initial load
        }
    };

    const handleNavigateToPayments = () => {
        navigate(AppRoute.PAYMENTS);
    };

    const handleNavigateToMarketplace = () => {
        navigate(AppRoute.MARKETPLACE);
    };

    const refreshConnection = async () => {
        setBackendStatus('checking');
        await checkBackendConnection();
        await loadSubscriptionStatus();
        
        if (backendStatus === 'online') {
            toast.success({
                message: 'Backend connection restored!',
            });
        }
    };

    // Show error page if backend is offline
    if (backendStatus === 'offline') {
        return (
            <BackendErrorPage 
                onRetry={refreshConnection}
                error="Unable to connect to the music platform backend. Please ensure the backend server is running on http://localhost:8000"
            />
        );
    }

    return (
        <ResponsiveLayout title="🎵 Music Platform">
            <Stack spacing="xl">
                {/* User Status */}
                {subscriptionStatus && (
                    <ResponsiveCard title="Your Account Status">
                        <Stack spacing="md">
                            <Stack direction="row" align="center" spacing="md">
                                <div style={{
                                    width: '12px',
                                    height: '12px',
                                    borderRadius: '50%',
                                    backgroundColor: subscriptionStatus.subscribed ? '#52c41a' : '#ff4d4f'
                                }} />
                                <Text weight="bold">
                                    {subscriptionStatus.subscribed ? 'Premium Subscriber' : 'Free Account'}
                                </Text>
                            </Stack>
                            {!subscriptionStatus.subscribed && (
                                <ResponsiveButton onClick={handleNavigateToPayments} fullWidth>
                                    Upgrade to Premium
                                </ResponsiveButton>
                            )}
                        </Stack>
                    </ResponsiveCard>
                )}

                {/* Main Actions */}
                <ResponsiveGrid columns={{ mobile: 1, tablet: 2, desktop: 3 }}>
                    <ResponsiveCard 
                        title="Browse Music" 
                        subtitle="Discover Ethiopian music"
                        onClick={handleNavigateToMarketplace}
                    >
                        <div style={{ fontSize: '48px', textAlign: 'center', marginBottom: '16px' }}>
                            🎧
                        </div>
                        <ResponsiveButton onClick={handleNavigateToMarketplace} fullWidth>
                            Browse Marketplace
                        </ResponsiveButton>
                    </ResponsiveCard>

                    <ResponsiveCard 
                        title="Manage Payments" 
                        subtitle="Subscribe or purchase"
                        onClick={handleNavigateToPayments}
                    >
                        <div style={{ fontSize: '48px', textAlign: 'center', marginBottom: '16px' }}>
                            💳
                        </div>
                        <ResponsiveButton onClick={handleNavigateToPayments} fullWidth>
                            Manage Payments
                        </ResponsiveButton>
                    </ResponsiveCard>

                    <ResponsiveCard title="Payment Methods">
                        <div style={{ fontSize: '48px', textAlign: 'center', marginBottom: '16px' }}>
                            📱
                        </div>
                        <Text size="sm" style={{ marginBottom: '12px' }}>
                            Multiple payment options including:
                        </Text>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                            {paymentProviders.slice(0, 2).map(provider => (
                                <div key={provider.id} style={{ 
                                    padding: '4px 8px', 
                                    backgroundColor: '#f0f0f0', 
                                    borderRadius: '4px',
                                    fontSize: '12px'
                                }}>
                                    {provider.name}
                                </div>
                            ))}
                        </div>
                    </ResponsiveCard>
                </ResponsiveGrid>

                {/* Features */}
                <ResponsiveCard title="Platform Features">
                    <ResponsiveGrid columns={{ mobile: 2, tablet: 3, desktop: 3 }}>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '24px', marginBottom: '8px' }}>🎵</div>
                            <Text size="sm">Ethiopian Music</Text>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '24px', marginBottom: '8px' }}>💰</div>
                            <Text size="sm">Affordable Pricing</Text>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '24px', marginBottom: '8px' }}>📱</div>
                            <Text size="sm">Mobile Payments</Text>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '24px', marginBottom: '8px' }}>🚀</div>
                            <Text size="sm">Fast Streaming</Text>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '24px', marginBottom: '8px' }}>🎧</div>
                            <Text size="sm">High Quality Audio</Text>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '24px', marginBottom: '8px' }}>🛡️</div>
                            <Text size="sm">Secure Payments</Text>
                        </div>
                    </ResponsiveGrid>
                </ResponsiveCard>
            </Stack>
        </ResponsiveLayout>
    );
};

export default MusicPlatformHome;
