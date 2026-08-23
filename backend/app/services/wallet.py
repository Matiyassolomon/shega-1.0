from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
import uuid
import logging

from app.models.financial import Wallet, Transaction, TransactionStatus
from app.services.ledger import LedgerService
from app.core.database import get_db

logger = logging.getLogger(__name__)

class WalletService:
    @staticmethod
    async def get_or_create_wallet(
        db: AsyncSession,
        user_id: uuid.UUID,
        currency: str = "ETB"
    ) -> Wallet:
        """Get or create user wallet"""
        result = await db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            wallet = Wallet(
                user_id=user_id,
                currency=currency
            )
            db.add(wallet)
            await db.flush()
        
        return wallet

    @staticmethod
    async def get_balance(
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> float:
        """Get user's current wallet balance"""
        wallet = await WalletService.get_or_create_wallet(db, user_id)
        return await LedgerService.get_balance(db, user_id, "wallet")

    @staticmethod
    async def credit(
        db: AsyncSession,
        user_id: uuid.UUID,
        amount: float,
        description: str = "",
        metadata: Dict = None,
        idempotency_key: str = None
    ) -> Transaction:
        """Credit user's wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Record transaction
        transaction = await LedgerService.record_transaction(
            db=db,
            user_id=user_id,
            transaction_type="credit",
            amount=amount,
            category="wallet",
            metadata=metadata,
            idempotency_key=idempotency_key
        )
        
        # Mark as completed
        await LedgerService.complete_transaction(db, transaction.id)
        await db.commit()
        
        return transaction

    @staticmethod
    async def debit(
        db: AsyncSession,
        user_id: uuid.UUID,
        amount: float,
        description: str = "",
        metadata: Dict = None,
        idempotency_key: str = None
    ) -> Transaction:
        """Debit user's wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Check sufficient balance
        balance = await WalletService.get_balance(db, user_id)
        if balance < amount:
            raise ValueError("Insufficient balance")
        
        # Record transaction
        transaction = await LedgerService.record_transaction(
            db=db,
            user_id=user_id,
            transaction_type="debit",
            amount=-amount,
            category="wallet",
            metadata=metadata,
            idempotency_key=idempotency_key
        )
        
        # Mark as completed
        await LedgerService.complete_transaction(db, transaction.id)
        await db.commit()
        
        return transaction

    @staticmethod
    async def transfer(
        db: AsyncSession,
        from_user_id: uuid.UUID,
        to_user_id: uuid.UUID,
        amount: float,
        description: str = "",
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Transfer funds between users"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if from_user_id == to_user_id:
            raise ValueError("Cannot transfer to self")
        
        # Check sender balance
        balance = await WalletService.get_balance(db, from_user_id)
        if balance < amount:
            raise ValueError("Insufficient balance")
        
        # Debit sender
        await WalletService.debit(
            db=db,
            user_id=from_user_id,
            amount=amount,
            description=f"Transfer to {to_user_id}: {description}",
            metadata=metadata
        )
        
        # Credit recipient
        await WalletService.credit(
            db=db,
            user_id=to_user_id,
            amount=amount,
            description=f"Transfer from {from_user_id}: {description}",
            metadata=metadata
        )
        
        await db.commit()
        
        return {
            "from_user": str(from_user_id),
            "to_user": str(to_user_id),
            "amount": amount,
            "status": "completed"
        }