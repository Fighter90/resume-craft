"""Add phone and city fields to users table.

Revision ID: 009_user_profile_fields
Revises: 008_score_breakdown
Create Date: 2026-03-10 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '009_user_profile_fields'
down_revision: str = '008_score_breakdown'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add profile fields for phone and city."""
    op.add_column('users', sa.Column('phone', sa.String(length=32), nullable=True))
    op.add_column('users', sa.Column('city', sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Remove profile fields for phone and city."""
    op.drop_column('users', 'city')
    op.drop_column('users', 'phone')
