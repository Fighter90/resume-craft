"""Fix old LLM provider 'all' error messages in rewrite_history.

Revision ID: 006_fix_llm_provider_all_messages
Revises: 005_email_verification
"""

from __future__ import annotations

from alembic import op

revision = '006_fix_llm_provider_all_messages'
down_revision = '005_email_verification'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        'UPDATE rewrite_history '
        "SET error_message = REPLACE(error_message, 'LLM-провайдер all', 'Все LLM-провайдеры') "
        "WHERE error_message LIKE '%LLM-провайдер all%'"
    )


def downgrade() -> None:
    # Обратная миграция: восстановить старый текст
    op.execute(
        'UPDATE rewrite_history '
        "SET error_message = REPLACE(error_message, 'Все LLM-провайдеры', 'LLM-провайдер all') "
        "WHERE error_message LIKE '%Все LLM-провайдеры%'"
    )
