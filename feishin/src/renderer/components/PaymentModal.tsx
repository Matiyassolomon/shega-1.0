import { useState } from 'react';

import { Button } from '/@/shared/components/button/button';
import { Group } from '/@/shared/components/group/group';
import { Stack } from '/@/shared/components/stack/stack';
import { Text } from '/@/shared/components/text/text';
import { toast } from '/@/shared/components/toast/toast';

type PaymentType = 'subscription_monthly' | 'wallet_topup' | 'song_purchase' | 'playlist_purchase';
type PaymentMethod = 'telebirr' | 'cbe' | 'wallet';

interface PaymentOption {
    id: PaymentType;
    title: string;
    description: string;
    amount: number;
    icon: string;
}

interface PaymentMethodOption {
    id: PaymentMethod;
    name: string;
    description: string;
    icon: string;
    recommended?: boolean;
}

interface PaymentModalProps {
    isOpen: boolean;
    onClose: () => void;
    itemType?: 'song' | 'playlist' | 'subscription' | 'wallet';
    itemId?: string;
    itemTitle?: string;
    itemPrice?: number;
    onPaymentComplete?: (paymentId: string) => void;
}

const PAYMENT_OPTIONS: PaymentOption[] = [
    {
        id: 'subscription_monthly',
        title: 'Premium Subscription',
        description: 'Unlimited access for one month',
        amount: 199,
        icon: '🎵',
    },
    {
        id: 'wallet_topup',
        title: 'Wallet Top-up',
        description: 'Add funds to your wallet',
        amount: 50,
        icon: '💰',
    },
    {
        id: 'song_purchase',
        title: 'Purchase Song',
        description: 'Buy individual track',
        amount: 25,
        icon: '🎧',
    },
    {
        id: 'playlist_purchase',
        title: 'Purchase Playlist',
        description: 'Buy entire playlist',
        amount: 100,
        icon: '📋',
    },
];

const PAYMENT_METHODS: PaymentMethodOption[] = [
    {
        id: 'telebirr',
        name: 'Telebirr',
        description: 'Fast mobile payment',
        icon: '📱',
        recommended: true,
    },
    {
        id: 'cbe',
        name: 'CBE Birr',
        description: 'Bank transfer',
        icon: '🏦',
    },
    {
        id: 'wallet',
        name: 'Wallet Balance',
        description: 'Use existing funds',
        icon: '💳',
    },
];

const PaymentModal = ({
    isOpen,
    onClose,
    itemType = 'subscription',
    itemId,
    itemTitle,
    itemPrice,
    onPaymentComplete,
}: PaymentModalProps) => {
    const [step, setStep] = useState<1 | 2 | 3>(1);
    const [selectedPaymentType, setSelectedPaymentType] = useState<PaymentType | null>(null);
    const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<PaymentMethod | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);

    if (!isOpen) return null;

    const handlePaymentTypeSelect = (option: PaymentOption) => {
        setSelectedPaymentType(option.id);
        setStep(2);
    };

    const handlePaymentMethodSelect = (method: PaymentMethod) => {
        setSelectedPaymentMethod(method);
        setStep(3);
    };

    const handleBack = () => {
        if (step === 3) {
            setStep(2);
        } else if (step === 2) {
            setStep(1);
        }
    };

    const handleConfirm = async () => {
        setIsProcessing(true);
        try {
            // Simulate payment processing
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            toast.success({
                message: 'Payment completed successfully',
                title: 'Payment Success',
            });
            
            onPaymentComplete?.('demo-payment-id');
            onClose();
            
            // Reset state
            setStep(1);
            setSelectedPaymentType(null);
            setSelectedPaymentMethod(null);
        } catch (error) {
            toast.error({
                message: 'Payment failed. Please try again.',
                title: 'Payment Error',
            });
        } finally {
            setIsProcessing(false);
        }
    };

    const getPaymentAmount = () => {
        if (itemPrice) return itemPrice;
        if (selectedPaymentType) {
            return PAYMENT_OPTIONS.find(opt => opt.id === selectedPaymentType)?.amount || 0;
        }
        return 0;
    };

    const formatPrice = (amount: number) => {
        return new Intl.NumberFormat('et-ET', {
            style: 'currency',
            currency: 'ETB',
        }).format(amount);
    };

    const renderStep1 = () => (
        <Stack gap="md">
            <Text fw={700} size="lg">Select Payment Type</Text>
            <Text variant="secondary">Choose what you want to pay for</Text>
            
            {PAYMENT_OPTIONS.map((option) => (
                <button
                    key={option.id}
                    onClick={() => handlePaymentTypeSelect(option)}
                    style={{
                        width: '100%',
                        padding: '16px',
                        background: 'var(--theme-colors-surface)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: 12,
                        cursor: 'pointer',
                        textAlign: 'left',
                        transition: 'all 0.2s',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.3)'}
                    onMouseLeave={(e) => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)'}
                >
                    <Stack gap="xs">
                        <div style={{ fontSize: '24px' }}>{option.icon}</div>
                        <Text fw={600}>{option.title}</Text>
                        <Text variant="secondary" size="sm">{option.description}</Text>
                        <Text fw={700} style={{ color: 'var(--consumer-accent, #f4c542)' }}>
                            {formatPrice(option.amount)}
                        </Text>
                    </Stack>
                </button>
            ))}
        </Stack>
    );

    const renderStep2 = () => (
        <Stack gap="md">
            <Text fw={700} size="lg">Select Payment Method</Text>
            <Text variant="secondary">Choose how you want to pay</Text>
            
            {PAYMENT_METHODS.map((method) => (
                <button
                    key={method.id}
                    onClick={() => handlePaymentMethodSelect(method.id)}
                    style={{
                        width: '100%',
                        padding: '16px',
                        background: selectedPaymentMethod === method.id 
                            ? 'rgba(29, 185, 84, 0.2)' 
                            : 'var(--theme-colors-surface)',
                        border: selectedPaymentMethod === method.id 
                            ? '2px solid #1DB954' 
                            : '1px solid rgba(255,255,255,0.1)',
                        borderRadius: 12,
                        cursor: 'pointer',
                        textAlign: 'left',
                        transition: 'all 0.2s',
                        position: 'relative',
                    }}
                    onMouseEnter={(e) => {
                        if (selectedPaymentMethod !== method.id) {
                            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.3)';
                        }
                    }}
                    onMouseLeave={(e) => {
                        if (selectedPaymentMethod !== method.id) {
                            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
                        }
                    }}
                >
                    <Stack gap="xs">
                        <div style={{ fontSize: '24px' }}>{method.icon}</div>
                        <Text fw={600}>{method.name}</Text>
                        <Text variant="secondary" size="sm">{method.description}</Text>
                        {method.recommended && (
                            <div style={{
                                position: 'absolute',
                                top: '12px',
                                right: '12px',
                                background: '#1DB954',
                                color: 'white',
                                padding: '4px 8px',
                                borderRadius: '12px',
                                fontSize: '10px',
                                fontWeight: 'bold',
                            }}>
                                RECOMMENDED
                            </div>
                        )}
                    </Stack>
                </button>
            ))}
        </Stack>
    );

    const renderStep3 = () => (
        <Stack gap="md">
            <Text fw={700} size="lg">Confirm Payment</Text>
            <Text variant="secondary">Review your payment details</Text>
            
            <Stack
                p="md"
                style={{
                    background: 'var(--theme-colors-surface)',
                    borderRadius: 12,
                    border: '1px solid rgba(255,255,255,0.1)',
                }}
                gap="sm"
            >
                {itemTitle && (
                    <>
                        <Text variant="secondary" size="sm">Item</Text>
                        <Text fw={600}>{itemTitle}</Text>
                    </>
                )}
                
                {selectedPaymentType && (
                    <>
                        <Text variant="secondary" size="sm">Payment Type</Text>
                        <Text>{PAYMENT_OPTIONS.find(opt => opt.id === selectedPaymentType)?.title}</Text>
                    </>
                )}
                
                {selectedPaymentMethod && (
                    <>
                        <Text variant="secondary" size="sm">Payment Method</Text>
                        <Text>{PAYMENT_METHODS.find(m => m.id === selectedPaymentMethod)?.name}</Text>
                    </>
                )}
                
                <div style={{ height: '1px', background: 'rgba(255,255,255,0.1)', margin: '8px 0' }} />
                
                <Text variant="secondary" size="sm">Total Amount</Text>
                <Text fw={700} size="xl" style={{ color: 'var(--consumer-accent, #f4c542)' }}>
                    {formatPrice(getPaymentAmount())}
                </Text>
            </Stack>
            
            <Text variant="secondary" size="sm" style={{ textAlign: 'center' }}>
                By confirming, you agree to complete this payment
            </Text>
        </Stack>
    );

    return (
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
            onClick={onClose}
        >
            <div
                style={{
                    background: 'var(--theme-colors-background, #121212)',
                    borderRadius: 20,
                    padding: '24px',
                    maxWidth: 500,
                    width: '100%',
                    maxHeight: '90vh',
                    overflowY: 'auto',
                    border: '1px solid rgba(255,255,255,0.1)',
                }}
                onClick={(e) => e.stopPropagation()}
            >
                <Stack gap="lg">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text fw={700} size="xl">Payment</Text>
                        <button
                            onClick={onClose}
                            style={{
                                background: 'none',
                                border: 'none',
                                color: 'rgba(255,255,255,0.7)',
                                fontSize: '24px',
                                cursor: 'pointer',
                                padding: '4px',
                            }}
                        >
                            ×
                        </button>
                    </div>

                    {/* Progress indicator */}
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        {[1, 2, 3].map((s) => (
                            <div
                                key={s}
                                style={{
                                    flex: 1,
                                    height: '4px',
                                    background: step >= s ? 'var(--consumer-accent, #f4c542)' : 'rgba(255,255,255,0.2)',
                                    borderRadius: '2px',
                                    transition: 'background 0.3s',
                                }}
                            />
                        ))}
                    </div>

                    {step === 1 && renderStep1()}
                    {step === 2 && renderStep2()}
                    {step === 3 && renderStep3()}

                    <Group>
                        {step > 1 && (
                            <Button
                                onClick={handleBack}
                                variant="default"
                                disabled={isProcessing}
                                style={{ flex: 1 }}
                            >
                                Back
                            </Button>
                        )}
                        {step === 3 && (
                            <Button
                                onClick={handleConfirm}
                                className="telegram-primary-btn"
                                disabled={isProcessing}
                                style={{ flex: 1 }}
                            >
                                {isProcessing ? 'Processing...' : `Pay ${formatPrice(getPaymentAmount())}`}
                            </Button>
                        )}
                    </Group>
                </Stack>
            </div>
        </div>
    );
};

export default PaymentModal;
