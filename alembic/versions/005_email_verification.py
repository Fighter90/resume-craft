"""Add is_verified to users table.

Revision ID: 005_email_verification
Revises: 004_resume_soft_delete
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = '005_email_verification'
down_revision = '004_resume_soft_delete'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users', sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False)
    )


def downgrade() -> None:
    op.drop_column('users', 'is_verified')
