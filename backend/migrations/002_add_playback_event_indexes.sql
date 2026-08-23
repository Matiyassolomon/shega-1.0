"""Add financial tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Create ENUM types
    op.execute("CREATE TYPE transactionstatus AS ENUM ('pending', 'processing', 'completed', 'failed', 'refunded', 'cancelled', 'held')")
    op.execute("CREATE TYPE transactiontype AS ENUM ('top_up', 'withdrawal', 'transfer', 'payment', 'refund', 'support', 'gift', 'purchase', 'earning', 'platform_fee')")
    op.execute("CREATE TYPE ledgerentrytype AS ENUM ('debit', 'credit')")

    # Create wallets table
    op.create_table(
        'wallets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default='ETB'),
        sa.Column('is_active', sa.Integer, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
        sa.Index('idx_wallets_user_id', 'user_id'),
    )

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('type', sa.Enum('top_up', 'withdrawal', 'transfer', 'payment', 'refund', 'support', 'gift', 'purchase', 'earning', 'platform_fee', name='transactiontype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', 'refunded', 'cancelled', 'held', name='transactionstatus'), nullable=False, server_default='pending'),
        sa.Column('amount', sa.Float, nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='ETB'),
        sa.Column('reference', sa.String(100), unique=True),
        sa.Column('idempotency_key', sa.String(100), unique=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('error_message', sa.Text),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
        sa.Index('idx_transactions_user_id', 'user_id'),
        sa.Index('idx_transactions_status', 'status'),
        sa.Index('idx_transactions_created_at', 'created_at'),
    )

    # Create ledger_entries table (immutable)
    op.create_table(
        'ledger_entries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('transaction_id', UUID(as_uuid=True), sa.ForeignKey('transactions.id'), nullable=False),
        sa.Column('entry_type', sa.Enum('debit', 'credit', name='ledgerentrytype'), nullable=False),
        sa.Column('amount', sa.Float, nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='ETB'),
        sa.Column('category', sa.String(50)),
        sa.Column('description', sa.String(500)),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Index('idx_ledger_user_id', 'user_id'),
        sa.Index('idx_ledger_transaction_id', 'transaction_id'),
        sa.Index('idx_ledger_created_at', 'created_at'),
    )

    # Create earnings table
    op.create_table(
        'earnings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('amount', sa.Float, nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='ETB'),
        sa.Column('source', sa.String(50)),
        sa.Column('source_id', UUID(as_uuid=True)),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('holding_until', sa.DateTime),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
        sa.Index('idx_earnings_user_id', 'user_id'),
        sa.Index('idx_earnings_status', 'status'),
    )

    # Create payout_requests table
    op.create_table(
        'payout_requests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('amount', sa.Float, nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='ETB'),
        sa.Column('payment_method', sa.String(50)),
        sa.Column('account_details', JSONB),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('reference', sa.String(100), unique=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('processed_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
        sa.Index('idx_payouts_user_id', 'user_id'),
        sa.Index('idx_payouts_status', 'status'),
    )

def downgrade():
    op.drop_table('payout_requests')
    op.drop_table('earnings')
    op.drop_table('ledger_entries')
    op.drop_table('transactions')
    op.drop_table('wallets')
    
    op.execute("DROP TYPE ledgerentrytype")
    op.execute("DROP TYPE transactiontype")
    op.execute("DROP TYPE transactionstatus")