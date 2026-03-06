"""Add soft-delete fields to users table.

Revision ID: 002_user_soft_delete
Revises: 001_initial
Create Date: 2025-01-15 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '002_user_soft_delete'
down_revision: str = '001_initial'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add deleted_at and scheduled_deletion columns to users."""
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('scheduled_deletion', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove soft-delete columns from users."""
    op.drop_column('users', 'scheduled_deletion')
    op.drop_column('users', 'deleted_at')
