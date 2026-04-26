// @ts-nocheck
import { useState, useEffect } from 'react';
import {
    purchaseSubscription,
    createPaymentIntent,
    processPayment,
    verifyPayment,
    getPaymentProviders,
    getSubscriptionTypes,
    getUserSubscription,
    checkUserSubscription,
    handleApiError,
    type PaymentIntent,
    type PaymentProcessResponse,
    type UserSubscriptionResponse,
    getBackendUserId,
    setBackendAccessToken,
    getBackendAccessToken,
} from '/@/renderer/api/refactored-client';
import { Button } from '/@/shared/components/button/button';
import { Stack } from '/@/shared/components/stack/stack';
import { Text } from '/@/shared/components/text/text';
import { toast } from '/@/shared/components/toast/toast';

const RefactoredPaymentsPage = () => {
    const userId = getBackendUserId();
    const [loading, setLoading] = useState(false);
    const [currentSubscription, setCurrentSubscription] = useState<UserSubscriptionResponse | null>(null);
    const [subscriptionStatus, setSubscriptionStatus] = useState<{ subscribed: boolean; subscription?: UserSubscriptionResponse } | null>(null);
    const [paymentIntent, setPaymentIntent] = useState<PaymentIntent | null>(null);
    const [paymentProcessing, setPaymentProcessing] = useState(false);
    const [selectedProvider, setSelectedProvider] = useState('telebirr');

    const paymentProviders = getPaymentProviders();
    const subscriptionTypes = getSubscriptionTypes();

    useEffect(() => {
        loadUserSubscription();
    }, [userId]);

    const loadUserSubscription = async () => {
        try {
            const status = await checkUserSubscription(userId);
            setSubscriptionStatus(status);
            if (status.subscribed && status.subscription) {
                setCurrentSubscription(status.subscription);
            }
        } catch (error) {
            console.error('Failed to load subscription status:', error);
        }
    };

    const handleSubscriptionPurchase = async (subscriptionType: string) => {
        setLoading(true);
        try {
            // Step 1: Create subscription purchase request
            const purchaseResult = await purchaseSubscription(subscriptionType, selectedProvider);
            
            if (purchaseResult.status === 'payment_required') {
                setPaymentIntent(purchaseResult.payment_intent);
                
                // Step 2: Process the payment
                const processResult = await processPayment(purchaseResult.payment_intent.id, {
                    payment_provider: selectedProvider,
                    return_url: `${window.location.origin}/payments/success`,
                    cancel_url: `${window.location.origin}/payments/cancel`,
                });

                if (processResult.status === 'requires_action') {
                    // Redirect to payment provider
                    if (processResult.payment_url) {
                        window.location.href = processResult.payment_url;
                    } else if (processResult.ussd_code) {
                        toast.success({
                            message: `Dial ${processResult.ussd_code} to complete payment`,
                            title: 'Payment Instructions',
                        });
                    }
                }
            }
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

    const handlePaymentVerification = async () => {
        if (!paymentIntent) return;

        setPaymentProcessing(true);
        try {
            // In a real implementation, this would get provider response from URL params
            const verificationResult = await verifyPayment(paymentIntent.id, {
                transaction_id: 'mock_transaction_id', // This would come from payment provider callback
            });

            if (verificationResult.verified) {
                toast.success({
                    message: 'Payment verified successfully!',
                    title: 'Payment Complete',
                });
                
                // Reload subscription status
                await loadUserSubscription();
                setPaymentIntent(null);
            } else {
                toast.error({
                    message: 'Payment verification failed',
                    title: 'Verification Error',
                });
            }
        } catch (error: any) {
            const apiError = handleApiError(error);
            toast.error({ 
                message: apiError.message, 
                title: 'Verification Failed' 
            });
        } finally {
            setPaymentProcessing(false);
        }
    };

    const formatPrice = (amount: number) => {
        return new Intl.NumberFormat('et-ET', {
            style: 'currency',
            currency: 'ETB',
        }).format(amount);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString();
    };

    const isSubscriptionActive = () => {
        if (!currentSubscription) return false;
        return currentSubscription.status === 'active' && 
               new Date(currentSubscription.expires_at || '') > new Date();
    };

    return (
        <Stack gap="lg" p="lg">
            <Text fw={700} size="xl">
                Premium Subscription
            </Text>

            {/* Current Subscription Status */}
            {subscriptionStatus && (
                <Stack className="telegram-panel" gap="md" p="md">
                    <Text fw={600}>Current Status</Text>
                    {subscriptionStatus.subscribed && currentSubscription ? (
                        <Stack gap="sm">
                            <Text size="sm" variant="secondary">
                                Subscription Type: {currentSubscription.subscription_type}
                            </Text>
                            <Text size="sm" variant="secondary">
                                Status: {currentSubscription.status}
                            </Text>
                            <Text size="sm" variant="secondary">
                                Expires: {formatDate(currentSubscription.expires_at || '')}
                            </Text>
                            {isSubscriptionActive() && (
                                <Text size="sm" className="text-green-500">
                                    ✅ Active
                                </Text>
                            )}
                        </Stack>
                    ) : (
                        <Text size="sm" variant="secondary">
                            No active subscription
                        </Text>
                    )}
                </Stack>
            )}

            {/* Payment Provider Selection */}
            <Stack className="telegram-panel" gap="md" p="md">
                <Text fw={600}>Payment Method</Text>
                <Stack gap="sm">
                    {paymentProviders.map((provider) => (
                        <Button
                            key={provider.id}
                            className={`telegram-secondary-btn ${selectedProvider === provider.id ? 'selected' : ''}`}
                            onClick={() => setSelectedProvider(provider.id)}
                            variant={selectedProvider === provider.id ? 'primary' : 'secondary'}
                        >
                            <Stack direction="row" gap="sm" align="center">
                                <Text>{provider.name}</Text>
                                <Text size="xs" variant="secondary">
                                    ({provider.description})
                                </Text>
                            </Stack>
                        </Button>
                    ))}
                </Stack>
            </Stack>

            {/* Subscription Options */}
            <Stack gap="md">
                <Text fw={600}>Available Plans</Text>
                {subscriptionTypes.map((plan) => (
                    <Stack key={plan.id} className="telegram-panel" gap="sm" p="md">
                        <Stack direction="row" justify="space-between" align="center">
                            <Text fw={600}>{plan.name}</Text>
                            <Text fw={700} size="lg" className="text-green-500">
                                {formatPrice(plan.price)}
                            </Text>
                        </Stack>
                        <Text size="sm" variant="secondary">
                            {plan.description}
                        </Text>
                        <Button
                            className="telegram-primary-btn"
                            onClick={() => handleSubscriptionPurchase(plan.id)}
                            disabled={loading || isSubscriptionActive()}
                        >
                            {loading ? 'Processing...' : 'Subscribe Now'}
                        </Button>
                    </Stack>
                ))}
            </Stack>

            {/* Payment Processing */}
            {paymentIntent && (
                <Stack className="telegram-panel" gap="md" p="md">
                    <Text fw={600}>Payment Processing</Text>
                    <Text size="sm" variant="secondary">
                        Payment Intent ID: {paymentIntent.id}
                    </Text>
                    <Text size="sm" variant="secondary">
                        Amount: {formatPrice(paymentIntent.amount)}
                    </Text>
                    <Text size="sm" variant="secondary">
                        Status: {paymentIntent.status}
                    </Text>
                    
                    <Button
                        className="telegram-primary-btn"
                        onClick={handlePaymentVerification}
                        disabled={paymentProcessing}
                    >
                        {paymentProcessing ? 'Verifying...' : 'Verify Payment'}
                    </Button>
                </Stack>
            )}

            {/* Features */}
            <Stack className="telegram-panel" gap="md" p="md">
                <Text fw={600}>Premium Features</Text>
                <Stack gap="sm">
                    <Text size="sm">✓ Unlimited premium tracks</Text>
                    <Text size="sm">✓ High-quality audio (320kbps)</Text>
                    <Text size="sm">✓ Offline downloads</Text>
                    <Text size="sm">✓ No advertisements</Text>
                    <Text size="sm">✓ Advanced search filters</Text>
                    <Text size="sm">✓ Exclusive content access</Text>
                </Stack>
            </Stack>
        </Stack>
    );
};

export default RefactoredPaymentsPage;
