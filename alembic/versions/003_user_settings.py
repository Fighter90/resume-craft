"""Create user_settings table for encrypted API keys.

Revision ID: 003_user_settings
Revises: 002_user_soft_delete
Create Date: 2025-01-15 01:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '003_user_settings'
down_revision: str = '002_user_soft_delete'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create user_settings table."""
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column(
            'user_id', sa.Uuid(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False
        ),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False, server_default=''),
        sa.Column('is_encrypted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint('id', name='pk_user_settings'),
        sa.UniqueConstraint('user_id', 'category', 'key', name='uq_user_settings_user_cat_key'),
    )
    op.create_index('ix_user_settings_user_id', 'user_settings', ['user_id'])


def downgrade() -> None:
    """Drop user_settings table."""
    op.drop_index('ix_user_settings_user_id', table_name='user_settings')
    op.drop_table('user_settings')
