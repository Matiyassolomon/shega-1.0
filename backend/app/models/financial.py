from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Enum, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

from app.models.models import Base

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    HELD = "held"

class TransactionType(str, enum.Enum):
    TOP_UP = "top_up"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    REFUND = "refund"
    SUPPORT = "support"
    GIFT = "gift"
    PURCHASE = "purchase"
    EARNING = "earning"
    PLATFORM_FEE = "platform_fee"

class LedgerEntryType(str, enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"

class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    currency = Column(String(3), default="ETB")
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="wallet")

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("idx_transactions_user_id", "user_id"),
        Index("idx_transactions_status", "status"),
        Index("idx_transactions_created_at", "created_at"),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="ETB")
    reference = Column(String(100), unique=True)
    idempotency_key = Column(String(100), unique=True)
    metadata = Column(JSONB, default={})
    error_message = Column(Text)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (
        Index("idx_ledger_user_id", "user_id"),
        Index("idx_ledger_transaction_id", "transaction_id"),
        Index("idx_ledger_created_at", "created_at"),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    entry_type = Column(Enum(LedgerEntryType), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="ETB")
    category = Column(String(50))  # wallet, earnings, platform_revenue, etc.
    description = Column(String(500))
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, server_default=func.now())
    
    # This is append-only - no updates allowed

class Earnings(Base):
    __tablename__ = "earnings"
    __table_args__ = (
        Index("idx_earnings_user_id", "user_id"),
        Index("idx_earnings_status", "status"),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="ETB")
    source = Column(String(50))  # stream, tip, gift, sale
    source_id = Column(UUID(as_uuid=True))  # Reference to source object
    status = Column(String(20), default="pending")  # pending, held, available, paid, failed
    holding_until = Column(DateTime)  # When earnings become available
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class PayoutRequest(Base):
    __tablename__ = "payout_requests"
    __table_args__ = (
        Index("idx_payouts_user_id", "user_id"),
        Index("idx_payouts_status", "status"),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="ETB")
    payment_method = Column(String(50))  # bank, mobile, telebirr
    account_details = Column(JSONB)  # Payment account info
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    reference = Column(String(100), unique=True)
    metadata = Column(JSONB, default={})
    processed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())