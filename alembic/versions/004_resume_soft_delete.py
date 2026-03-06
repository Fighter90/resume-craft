"""Add soft-delete to resumes (deleted_at column).

Revision ID: 004_resume_soft_delete
Revises: 003_user_settings
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = '004_resume_soft_delete'
down_revision = '003_user_settings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('resumes', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('resumes', 'deleted_at')
