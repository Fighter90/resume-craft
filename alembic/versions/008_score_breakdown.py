"""Add score_breakdown JSONB column to rewrite_history.

Revision ID: 008_score_breakdown
Revises: 007_user_avatar
Create Date: 2025-07-14 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = '008_score_breakdown'
down_revision: str = '007_user_avatar'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('rewrite_history', sa.Column('score_breakdown', JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column('rewrite_history', 'score_breakdown')
