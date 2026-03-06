"""Add soft-delete to resumes (deleted_at column).

Revision ID: 004
Revises: 003
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('resumes', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('resumes', 'deleted_at')
