from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging

from app.models.financial import (
    LedgerEntry, Transaction, LedgerEntryType,
    TransactionStatus, Wallet, Earnings
)
from app.core.database import get_db

logger = logging.getLogger(__name__)

class LedgerService:
    @staticmethod
    async def get_balance(
        db: AsyncSession,
        user_id: uuid.UUID,
        category: str = "wallet"
    ) -> float:
        """Calculate balance from ledger entries"""
        result = await db.execute(
            select(
                func.sum(LedgerEntry.amount)
            ).where(
                and_(
                    LedgerEntry.user_id == user_id,
                    LedgerEntry.category == category
                )
            )
        )
        return result.scalar() or 0.0

    @staticmethod
    async def create_ledger_entry(
        db: AsyncSession,
        user_id: uuid.UUID,
        transaction_id: uuid.UUID,
        entry_type: LedgerEntryType,
        amount: float,
        currency: str = "ETB",
        category: str = "wallet",
        description: str = "",
        metadata: Dict = None
    ) -> LedgerEntry:
        """Create an append-only ledger entry"""
        entry = LedgerEntry(
            user_id=user_id,
            transaction_id=transaction_id,
            entry_type=entry_type,
            amount=amount,
            currency=currency,
            category=category,
            description=description,
            metadata=metadata or {}
        )
        db.add(entry)
        return entry

    @staticmethod
    async def record_transaction(
        db: AsyncSession,
        user_id: uuid.UUID,
        transaction_type: str,
        amount: float,
        category: str = "wallet",
        metadata: Dict = None,
        idempotency_key: str = None
    ) -> Transaction:
        """Record a financial transaction with ledger entries"""
        # Check idempotency
        if idempotency_key:
            existing = await db.execute(
                select(Transaction).where(
                    Transaction.idempotency_key == idempotency_key
                )
            )
            if existing.scalar_one_or_none():
                return existing.scalar_one()
        
        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            type=transaction_type,
            status=TransactionStatus.PENDING,
            amount=amount,
            currency="ETB",
            idempotency_key=idempotency_key,
            metadata=metadata or {}
        )
        db.add(transaction)
        await db.flush()
        
        # Create ledger entry
        entry_type = LedgerEntryType.DEBIT if amount < 0 else LedgerEntryType.CREDIT
        await LedgerService.create_ledger_entry(
            db=db,
            user_id=user_id,
            transaction_id=transaction.id,
            entry_type=entry_type,
            amount=abs(amount),
            category=category,
            description=f"{transaction_type} transaction"
        )
        
        # Update wallet balance (optional - can calculate from ledger)
        # We'll calculate balance from ledger entries
        
        return transaction

    @staticmethod
    async def complete_transaction(
        db: AsyncSession,
        transaction_id: uuid.UUID
    ) -> Transaction:
        """Mark a transaction as completed"""
        transaction = await db.get(Transaction, transaction_id)
        if not transaction:
            raise ValueError("Transaction not found")
        
        transaction.status = TransactionStatus.COMPLETED
        transaction.completed_at = datetime.utcnow()
        return transaction

    @staticmethod
    async def get_transaction_history(
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        """Get user's transaction history"""
        result = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_ledger_entries(
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[LedgerEntry]:
        """Get user's ledger entries"""
        result = await db.execute(
            select(LedgerEntry)
            .where(LedgerEntry.user_id == user_id)
            .order_by(LedgerEntry.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()