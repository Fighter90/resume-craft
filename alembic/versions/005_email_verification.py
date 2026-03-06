"""Add is_verified to users table.

Revision ID: 005
Revises: 004
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'is_verified')
