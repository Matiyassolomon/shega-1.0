/**
 * QuickPayModal - 3-Step Payment Flow
 * Step 1: Select payment method (Card/Mobile/PayPal)
 * Step 2: Confirm amount and pay
 * Step 3: Success/Done
 */
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { CgSpinnerTwo } from 'react-icons/cg';
import { LuCheck, LuCreditCard, LuSmartphone, LuWallet, LuX } from 'react-icons/lu';

import styles from './QuickModal.module.css';

interface QuickPayModalProps {
  isOpen: boolean;
  onClose: () => void;
  amount: number;
  currency?: string;
  itemName: string;
  onPay: (method: string) => Promise<void>;
}

type PaymentStep = 'method' | 'confirm' | 'success';
type PaymentMethod = 'card' | 'mobile' | 'paypal';

export const QuickPayModal: React.FC<QuickPayModalProps> = ({
  isOpen,
  onClose,
  amount,
  currency = '$',
  itemName,
  onPay,
}) => {
  const { t } = useTranslation();
  const [step, setStep] = useState<PaymentStep>('method');
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleMethodSelect = (method: PaymentMethod) => {
    setSelectedMethod(method);
    setError(null);
    setStep('confirm');
  };

  const handlePay = async () => {
    if (!selectedMethod) return;
    setIsProcessing(true);
    setError(null);
    try {
      await onPay(selectedMethod);
      setStep('success');
    } catch (error) {
      setError(error instanceof Error ? error.message : t('pay.failed', 'Payment failed. Please try again.'));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClose = () => {
    setStep('method');
    setSelectedMethod(null);
    setError(null);
    onClose();
  };

  const methods: { id: PaymentMethod; icon: React.ReactNode; label: string }[] = [
    { id: 'card', icon: <LuCreditCard size={24} />, label: t('common.card', 'Card') },
    { id: 'mobile', icon: <LuSmartphone size={24} />, label: t('common.mobile', 'Mobile') },
    { id: 'paypal', icon: <LuWallet size={24} />, label: 'PayPal' },
  ];

  return (
    <div className={styles.overlay} role="dialog" aria-modal="true">
      <div className={styles.panel}>
        <div className={styles.header}>
          <h2 className={styles.title}>
            {step === 'method' && t('pay.selectMethod', 'Pay')} {itemName}
            {step === 'confirm' && t('pay.confirm', 'Confirm')}
            {step === 'success' && t('pay.success', 'Done!')}
          </h2>
          <button
            aria-label={t('common.close', 'Close')}
            onClick={handleClose}
            className={styles.iconButton}
          >
            <LuX size={20} />
          </button>
        </div>

        {step === 'method' && (
          <div className={styles.body}>
            <p className={styles.amount}>
              {currency}{amount.toFixed(2)}
            </p>
            {methods.map((method) => (
              <button
                key={method.id}
                onClick={() => handleMethodSelect(method.id)}
                className={styles.option}
              >
                <span className={styles.optionIcon}>{method.icon}</span>
                <span>{method.label}</span>
              </button>
            ))}
          </div>
        )}

        {step === 'confirm' && selectedMethod && (
          <div className={styles.body}>
            <div className={styles.center}>
              <p className={styles.muted}>{t('pay.amount', 'Amount')}</p>
              <p className={styles.amountLarge}>{currency}{amount.toFixed(2)}</p>
            </div>
            <div className={styles.summary}>
              {methods.find(m => m.id === selectedMethod)?.icon}
              <span>{methods.find(m => m.id === selectedMethod)?.label}</span>
            </div>
            {error && <p className={styles.error}>{error}</p>}
            <button
              onClick={handlePay}
              disabled={isProcessing}
              className={styles.primaryButton}
            >
              {isProcessing ? (
                <>
                  <CgSpinnerTwo size={20} className={styles.spinner} />
                  {t('pay.processing', 'Processing...')}
                </>
              ) : (
                t('pay.payNow', 'Pay Now')
              )}
            </button>
            <button
              onClick={() => setStep('method')}
              className={styles.secondaryButton}
            >
              {t('common.back', 'Back')}
            </button>
          </div>
        )}

        {step === 'success' && (
          <div className={styles.bodySuccess}>
            <div className={styles.successIcon}>
              <LuCheck size={40} />
            </div>
            <div>
              <h3 className={styles.successTitle}>
                {t('pay.paymentSuccessful', 'Payment Successful!')}
              </h3>
              <p className={styles.muted}>{t('pay.youPaid', 'You paid')} {currency}{amount.toFixed(2)}</p>
            </div>
            <button
              onClick={handleClose}
              className={styles.successButton}
            >
              {t('common.done', 'Done')}
            </button>
          </div>
        )}

        <div className={styles.steps}>
          {(['method', 'confirm', 'success'] as PaymentStep[]).map((s, i) => (
            <div
              key={s}
              className={[
                styles.step,
                step === s ? styles.currentStep :
                ['method', 'confirm', 'success'].indexOf(step) > i ? styles.completeStep : '',
              ].filter(Boolean).join(' ')}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default QuickPayModal;
