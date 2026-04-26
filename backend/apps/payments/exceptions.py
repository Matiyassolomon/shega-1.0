# apps/payments/exceptions.py
from typing import Optional, Dict, Any
from fastapi import HTTPException


class PaymentError(Exception):
    \"\"\"
    Base exception for all payment-related errors.
    Provides structured error information for API responses.
    \"\"\"
    status_code: int = 500
    error_code: str = \"PAYMENT_ERROR\"
    message: str = \"An error occurred during payment processing\"
    
    def __init__(
        self,
        message: Optional[str] = None,
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        self.status_code = status_code or self.status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            \"error\": {
                \"code\": self.error_code,
                \"message\": self.message,
                \"details\": self.details
            }
        }


class ProviderUnavailableError(PaymentError):
    \"\"\"Payment provider (Telebirr, Chapa, etc.) is unavailable.\"\"\"
    status_code = 503
    error_code = \"PROVIDER_UNAVAILABLE\"
    message = \"Payment provider is currently unavailable\"


class SignatureVerificationError(PaymentError):
    \"\"\"Webhook signature verification failed.\"\"\"
    status_code = 401
    error_code = \"INVALID_SIGNATURE\"
    message = \"Webhook signature verification failed\"


class PaymentNotFoundError(PaymentError):
    \"\"\"Payment record not found in database.\"\"\"
    status_code = 404
    error_code = \"PAYMENT_NOT_FOUND\"
    message = \"Payment not found\"


class DuplicatePaymentError(PaymentError):
    \"\"\"Duplicate payment attempt detected.\"\"\"
    status_code = 409
    error_code = \"DUPLICATE_PAYMENT\"
    message = \"Duplicate payment detected\"


class InvalidPaymentStateError(PaymentError):
    \"\"\"Payment is in an invalid state for the requested operation.\"\"\"
    status_code = 400
    error_code = \"INVALID_PAYMENT_STATE\"
    message = \"Payment cannot be processed in current state\"


class InsufficientFundsError(PaymentError):
    \"\"\"Insufficient funds for payment.\"\"\"
    status_code = 402
    error_code = \"INSUFFICIENT_FUNDS\"
    message = \"Insufficient funds to complete payment\"


class CurrencyNotSupportedError(PaymentError):
    \"\"\"Currency not supported by provider.\"\"\"
    status_code = 400
    error_code = \"CURRENCY_NOT_SUPPORTED\"
    message = \"Currency not supported by payment provider\"


class ValidationError(PaymentError):
    \"\"\"Payment data validation failed.\"\"\"
    status_code = 422
    error_code = \"VALIDATION_ERROR\"
    message = \"Payment validation failed\"


class ConfigurationError(PaymentError):
    \"\"\"Payment system misconfiguration.\"\"\"
    status_code = 500
    error_code = \"CONFIGURATION_ERROR\"
    message = \"Payment system configuration error\"


class RefundError(PaymentError):
    \"\"\"Refund processing failed.\"\"\"
    status_code = 400
    error_code = \"REFUND_FAILED\"
    message = \"Refund processing failed\"


class TimeoutError(PaymentError):
    \"\"\"Payment operation timed out.\"\"\"
    status_code = 504
    error_code = \"TIMEOUT\"
    message = \"Payment operation timed out\"
