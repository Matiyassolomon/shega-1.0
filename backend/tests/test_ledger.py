import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from app.models.financial import Transaction, LedgerEntry, Wallet
from app.services.ledger import LedgerService
from app.services.wallet import WalletService

@pytest.mark.asyncio
async def test_create_transaction(db_session: AsyncSession):
    user_id = uuid.uuid4()
    
    # Create wallet
    wallet = await WalletService.get_or_create_wallet(db_session, user_id)
    
    # Credit
    transaction = await WalletService.credit(
        db_session,
        user_id=user_id,
        amount=100.0,
        description="Test credit"
    )
    
    assert transaction.amount == 100.0
    assert transaction.status == "completed"
    
    # Check balance
    balance = await WalletService.get_balance(db_session, user_id)
    assert balance == 100.0
    
    # Debit
    transaction = await WalletService.debit(
        db_session,
        user_id=user_id,
        amount=30.0,
        description="Test debit"
    )
    
    # Check balance
    balance = await WalletService.get_balance(db_session, user_id)
    assert balance == 70.0
    
    # Check ledger entries
    entries = await LedgerService.get_ledger_entries(db_session, user_id)
    assert len(entries) == 2

@pytest.mark.asyncio
async def test_idempotency(db_session: AsyncSession):
    user_id = uuid.uuid4()
    idempotency_key = "test_key_123"
    
    # First transaction
    transaction1 = await WalletService.credit(
        db_session,
        user_id=user_id,
        amount=100.0,
        idempotency_key=idempotency_key
    )
    
    # Second transaction with same key
    transaction2 = await WalletService.credit(
        db_session,
        user_id=user_id,
        amount=100.0,
        idempotency_key=idempotency_key
    )
    
    # Should return the same transaction
    assert transaction1.id == transaction2.id
    assert transaction1.amount == transaction2.amount
    
    # Balance should only be credited once
    balance = await WalletService.get_balance(db_session, user_id)
    assert balance == 100.0

@pytest.mark.asyncio
async def test_insufficient_balance(db_session: AsyncSession):
    user_id = uuid.uuid4()
    
    # Try to debit without balance
    with pytest.raises(ValueError, match="Insufficient balance"):
        await WalletService.debit(
            db_session,
            user_id=user_id,
            amount=50.0
        )