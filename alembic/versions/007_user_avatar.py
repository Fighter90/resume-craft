"""Add avatar_url field to users table.

Revision ID: 007_user_avatar
Revises: 006_fix_llm_provider_all_messages
Create Date: 2025-01-20 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '007_user_avatar'
down_revision: str = '006_fix_llm_all_msg'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add avatar_url column to users."""
    op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))


def downgrade() -> None:
    """Remove avatar_url column from users."""
    op.drop_column('users', 'avatar_url')
