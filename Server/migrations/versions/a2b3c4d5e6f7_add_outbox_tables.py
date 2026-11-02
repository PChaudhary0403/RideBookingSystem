"""add outbox and processed_events tables

Revision ID: a2b3c4d5e6f7
Revises: 17a5363f12c4
Create Date: 2026-11-02 10:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = '17a5363f12c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create outbox_events and processed_events tables."""

    # Transactional Outbox table
    op.create_table(
        'outbox_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.String(36), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('aggregate_type', sa.String(50), nullable=False),
        sa.Column('aggregate_id', sa.String(100), nullable=False),
        sa.Column('topic', sa.String(200), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False,
                  server_default=sa.text('0')),
        sa.Column('max_retries', sa.Integer(), nullable=False,
                  server_default=sa.text('5')),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False,
                  server_default=sa.text("'pending'")),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id'),
        sa.CheckConstraint(
            "status IN ('pending', 'published', 'failed')",
            name='ck_outbox_status',
        ),
    )

    # Indexes for outbox polling
    op.create_index(
        'idx_outbox_pending',
        'outbox_events',
        ['status', 'created_at'],
    )
    op.create_index(
        'idx_outbox_failed',
        'outbox_events',
        ['status', 'retry_count'],
    )

    # Idempotent consumer deduplication table
    op.create_table(
        'processed_events',
        sa.Column('event_id', sa.String(36), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('consumer_group', sa.String(100), nullable=False,
                  server_default=sa.text("''")),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('event_id'),
    )

    # Cleanup index for processed events
    op.create_index(
        'idx_processed_events_cleanup',
        'processed_events',
        ['processed_at'],
    )


def downgrade() -> None:
    """Drop outbox_events and processed_events tables."""
    op.drop_index('idx_processed_events_cleanup', table_name='processed_events')
    op.drop_table('processed_events')

    op.drop_index('idx_outbox_failed', table_name='outbox_events')
    op.drop_index('idx_outbox_pending', table_name='outbox_events')
    op.drop_table('outbox_events')
