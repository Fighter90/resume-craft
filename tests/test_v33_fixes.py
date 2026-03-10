"""Тесты V33 (QA Report #29).

Покрывает:
- KEY-CHECK-001 (P0): убран client-side pre-check в ModelsPage
- VACANCY-PLACEHOLDER-001 (P3): auto-prefill title на VacancyPage
- GROQ-CASE-001 (P4): корректное имя Groq в ошибках
"""

from __future__ import annotations

from pathlib import Path


def test_llm_auth_error_uses_groq_display_name() -> None:
    """GROQ-CASE-001: имя провайдера должно быть `Groq`, не `groq`."""
    from app.core.exceptions import LLMAuthError

    err = LLMAuthError('groq')
    assert err.message == 'API-ключ для Groq не настроен'


def test_rewrite_router_has_display_name_map_for_groq() -> None:
    """Router pre-check должен использовать display name map для Groq."""
    src = Path('src/app/rewriter/router.py').read_text(encoding='utf-8')
    assert "'groq': 'Groq'" in src
    assert "detail=f'API-ключ для {display_name} не настроен." in src


def test_models_page_does_not_block_by_available_flag() -> None:
    """KEY-CHECK-001: кнопка запуска не должна блокироваться по local available-флагу."""
    src = Path('frontend/src/pages/wizard/ModelsPage.tsx').read_text(encoding='utf-8')
    assert 'Always send request to backend' in src
    assert 'disabled={loading}' in src
    assert 'selectedModel && !selectedModel.available' not in src


def test_vacancy_page_prefills_title_from_resume() -> None:
    """VACANCY-PLACEHOLDER-001: VacancyPage загружает резюме и проставляет manualTitle."""
    src = Path('frontend/src/pages/wizard/VacancyPage.tsx').read_text(encoding='utf-8')
    assert 'api.getResume(resumeId)' in src
    assert 'setManualTitle(' in src
    assert 'parsed.position' in src
    assert 'parsed.target_position' in src
    assert 'parsed.desired_position' in src
