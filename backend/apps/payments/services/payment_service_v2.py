"""
Payment Service with Repository Pattern
Database-agnostic business logic layer
"""
from typing import Optional, Dict, Any, List
from decimal import Decimal
import logging

from apps.payments.repositories.base import PaymentRepositoryInterface
from apps.payments.exceptions import (
    PaymentError, PaymentNotFoundError, InvalidPaymentStateError,
    ProviderUnavailableError, ValidationError
)
from apps.payments.schemas import PaymentCreate, PaymentResponse, PaymentStatusEnum

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Database-agnostic payment service using Repository Pattern.
    
    Benefits:
    - Testable with mock repositories (no live DB needed)
    - Swappable storage backends (Postgres, Mongo, in-memory)
    - Independent of SQLAlchemy/ORM
    - Clean separation of concerns
    """
    
    def __init__(self, repository: PaymentRepositoryInterface):
        self.repo = repository
    
    async def create_payment_intent(
        self, payment_data: PaymentCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> PaymentResponse:
        """Create a new payment intent."""
        if payment_data.amount <= 0:
            raise ValidationError("Amount must be greater than 0")
        
        payment_dict = payment_data.model_dump()
        payment_dict.update({
            "ip_address": ip_address,
            "user_agent": user_agent
        })
        
        result = await self.repo.create_payment(payment_dict)
        return PaymentResponse(**result)
    
    async def get_payment(self, payment_id: str) -> PaymentResponse:
        """Get payment by ID."""
        result = await self.repo.get_payment_by_id(payment_id)
        if not result:
            raise PaymentNotFoundError(f"Payment {payment_id} not found")
        return PaymentResponse(**result)
    
    async def confirm_payment(
        self, payment_id: str,
        provider_response: Dict[str, Any]
    ) -> PaymentResponse:
        """Confirm payment after provider callback."""
        payment = await self.get_payment(payment_id)
        
        if payment.status != PaymentStatusEnum.PENDING:
            raise InvalidPaymentStateError(
                f"Cannot confirm payment in status {payment.status}"
            )
        
        await self.repo.update_payment_status(
            payment_id,
            PaymentStatusEnum.COMPLETED,
            metadata=provider_response
        )
        
        return await self.get_payment(payment_id)
    
    async def fail_payment(
        self, payment_id: str,
        error_code: str,
        error_message: str
    ) -> PaymentResponse:
        """Mark payment as failed."""
        await self.repo.update_payment_status(
            payment_id,
            PaymentStatusEnum.FAILED,
            metadata={"error_code": error_code, "error_message": error_message}
        )
        return await self.get_payment(payment_id)
    
    async def list_user_payments(
        self, user_id: str,
        status: Optional[str] = None,
        limit: int = 20, offset: int = 0
    ) -> List[PaymentResponse]:
        """List payments for a user."""
        results = await self.repo.list_payments(
            user_id=user_id, status=status, limit=limit, offset=offset
        )
        return [PaymentResponse(**r) for r in results]
