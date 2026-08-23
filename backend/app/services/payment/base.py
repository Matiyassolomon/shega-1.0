from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

class PaymentProvider(ABC):
    """Abstract interface for all payment providers"""
    
    @abstractmethod
    async def initiate_payment(
        self,
        amount: float,
        currency: str,
        reference: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create payment intent"""
        pass
    
    @abstractmethod
    async def verify_payment(
        self,
        reference: str,
        provider_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify payment status"""
        pass
    
    @abstractmethod
    async def handle_webhook(
        self,
        raw_body: bytes,
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Process webhook callback"""
        pass
    
    @abstractmethod
    async def refund_payment(
        self,
        reference: str,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """Refund a payment"""
        pass

class PaymentError(Exception):
    def __init__(self, message: str, provider: str = None, code: str = None):
        self.message = message
        self.provider = provider
        self.code = code
        super().__init__(message)