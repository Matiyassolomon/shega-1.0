/**
 * PaymentModal
 * Displays when song requires purchase
 * Uses Feishin's existing modal styling
 * File: src/renderer/components/payment-modal.tsx
 */
import React from 'react';
import { shegaApi } from '../api/shega';

interface PaymentModalProps {
  isOpen: boolean;
  song: {
    id: string;
    title: string;
    artist: string;
    preview_url?: string;
  };
  options: {
    individual: {
      price: number;
      currency: string;
    };
    subscription?: {
      available: boolean;
      tiers: string[];
    };
  };
  onClose: () => void;
  onPurchaseComplete?: () => void;
}

export const PaymentModal: React.FC<PaymentModalProps> = ({
  isOpen,
  song,
  options,
  onClose,
  onPurchaseComplete,
}) => {
  if (!isOpen) return null;

  const handlePurchase = async () => {
    try {
      const intent: any = await shegaApi.createPaymentIntent(song.id);
      
      if (intent.redirect_url) {
        window.open(intent.redirect_url, '_blank');
      }
      
      // Poll for payment completion (simplified)
      setTimeout(() => {
        onPurchaseComplete?.();
      }, 5000);
    } catch (error) {
      console.error('Payment failed:', error);
    }
  };

  // Match Feishin's modal classes (use their existing styling)
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content payment-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}></button>
        
        <div className="payment-preview">
          <h3>{song.title}</h3>
          <p className="artist">{song.artist}</p>
          
          {song.preview_url && (
            <audio controls src={song.preview_url} className="preview-player">
              Preview not available
            </audio>
          )}
          <p className="preview-label">30-second preview</p>
        </div>

        <div className="payment-options">
          <div className="purchase-option">
            <h4>Buy This Song</h4>
            <p className="price">{options.individual.currency} {options.individual.price}</p>
            <p className="description">Own forever  Download included</p>
            <button className="btn-primary" onClick={handlePurchase}>
              Purchase
            </button>
          </div>

          {options.subscription?.available && (
            <div className="subscription-option">
              <h4>Get Premium</h4>
              <p>Unlock all songs with {options.subscription.tiers[0]}</p>
              <button className="btn-secondary">
                Upgrade
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
