"""Initial migration: users, resumes, vacancies, rewrite_history.

Revision ID: 001_initial
Revises: None
Create Date: 2025-01-01 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables."""
    # Расширения PostgreSQL
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')

    # --- users ---
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('plan', sa.String(10), nullable=False, server_default='free'),
        sa.Column('optimizations_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_users'),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # --- resumes ---
    op.create_table(
        'resumes',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_format', sa.String(10), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('parsed_data', JSONB(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_resumes'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_resumes_user_id_users', ondelete='CASCADE'),
    )
    op.create_index('ix_resumes_user_id', 'resumes', ['user_id'])
    op.create_index('ix_resumes_status', 'resumes', ['status'])

    # --- vacancies ---
    op.create_table(
        'vacancies',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('hh_id', sa.String(20), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('requirements', JSONB(), nullable=True),
        sa.Column('key_skills', JSONB(), nullable=True),
        sa.Column('salary_from', sa.Integer(), nullable=True),
        sa.Column('salary_to', sa.Integer(), nullable=True),
        sa.Column('experience', sa.String(50), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_vacancies'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_vacancies_user_id_users', ondelete='CASCADE'),
    )
    op.create_index('ix_vacancies_user_id', 'vacancies', ['user_id'])
    op.create_index('ix_vacancies_hh_id', 'vacancies', ['hh_id'])

    # --- rewrite_history ---
    op.create_table(
        'rewrite_history',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('resume_id', sa.Uuid(), nullable=False),
        sa.Column('vacancy_id', sa.Uuid(), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=True),
        sa.Column('rewritten_text', sa.Text(), nullable=True),
        sa.Column('rewritten_data', JSONB(), nullable=True),
        sa.Column('model_name', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('match_score_before', sa.Float(), nullable=True),
        sa.Column('match_score_after', sa.Float(), nullable=True),
        sa.Column('ats_rating', sa.String(2), nullable=True),
        sa.Column('keywords_added', JSONB(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_rewrite_history'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_rewrite_history_user_id_users', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], name='fk_rewrite_history_resume_id_resumes', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vacancy_id'], ['vacancies.id'], name='fk_rewrite_history_vacancy_id_vacancies', ondelete='CASCADE'),
    )
    op.create_index('ix_rewrite_history_user_id', 'rewrite_history', ['user_id'])
    op.create_index('ix_rewrite_history_resume_id', 'rewrite_history', ['resume_id'])
    op.create_index('ix_rewrite_history_vacancy_id', 'rewrite_history', ['vacancy_id'])
    op.create_index('ix_rewrite_history_status', 'rewrite_history', ['status'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('rewrite_history')
    op.drop_table('vacancies')
    op.drop_table('resumes')
    op.drop_table('users')
    op.execute('DROP EXTENSION IF EXISTS "vector"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
