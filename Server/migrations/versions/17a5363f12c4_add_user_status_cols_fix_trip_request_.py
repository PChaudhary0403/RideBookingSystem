"""add_user_status_cols_fix_trip_request_constraints

Revision ID: 17a5363f12c4
Revises:
Create Date: 2026-10-23 23:34:03.606106

Changes applied:
  - users: add is_online (bool, default false), is_available (bool, default false), last_seen (timestamptz)
  - trip_requests: add non-unique indexes on driver_id and user_id
    (unique constraints were already absent from the live DB; indexes improve query perf)
  - ride_requests: create the ride_requests table (future use)

Intentionally skipped (existing data has nulls — enforce later via a data backfill migration):
  - riders.email NOT NULL
  - riders.rating type change / NOT NULL
  - riders.total_reviews NOT NULL
  - active_drivers.last_seen NOT NULL / type change
  - active_drivers.is_available NOT NULL
  - user_locations.updated_at nullability change
  - users.phone / users.emailID NOT NULL (will be enforced after data cleanup)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '17a5363f12c4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply safe schema changes only."""

    # ── users table: add online/availability status columns ────────────────
    # server_default='false' ensures existing rows satisfy the NOT NULL constraint.
    op.add_column('users', sa.Column(
        'is_online', sa.Boolean(), nullable=False, server_default='false'
    ))
    op.add_column('users', sa.Column(
        'is_available', sa.Boolean(), nullable=False, server_default='false'
    ))
    op.add_column('users', sa.Column(
        'last_seen', sa.DateTime(timezone=True), nullable=True
    ))

    # ── trip_requests: add performance indexes ─────────────────────────────
    # The unique constraints were already removed from the live DB
    # (they caused IntegrityError on repeat bookings). Adding plain indexes now.
    op.create_index(
        op.f('ix_trip_requests_driver_id'), 'trip_requests', ['driver_id'], unique=False
    )
    op.create_index(
        op.f('ix_trip_requests_user_id'), 'trip_requests', ['user_id'], unique=False
    )

    # ── ride_requests: create table (future use) ───────────────────────────
    op.create_table(
        'ride_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('pickup_latitude', sa.Float(), nullable=False),
        sa.Column('pickup_longitude', sa.Float(), nullable=False),
        sa.Column('destination_latitude', sa.Float(), nullable=False),
        sa.Column('destination_longitude', sa.Float(), nullable=False),
        sa.Column('request_time', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['driver_id'], ['riders.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Reverse all changes applied in upgrade()."""

    op.drop_table('ride_requests')

    op.drop_index(op.f('ix_trip_requests_user_id'), table_name='trip_requests')
    op.drop_index(op.f('ix_trip_requests_driver_id'), table_name='trip_requests')

    op.drop_column('users', 'last_seen')
    op.drop_column('users', 'is_available')
    op.drop_column('users', 'is_online')
