# AGENT_FIX_PROMPT_V27

> Промт для AI-агента на доработку проекта ResumeCraft.ru
> Создан на основе QA Report #22 (22_FULL_RETEST_V27.md)
> Дата: 09.03.2026

---

## КОНТЕКСТ

Проведён полный ретест V27 с фокусом на Параметры оптимизации (AI-тогглы, сброс, сохранение).
**Результат: 5 из 7 багов V26 ИСПРАВЛЕНЫ.** EMAIL-VERIFY-001 исправлен. GROQ-KEY подтверждён.

Обнаружен **1 НОВЫЙ КРИТИЧНЫЙ баг** (RESET-001) и 1 minor (OPENAI-O4MINI).

Остались 4 проблемы:
1. **RESET-001** — кнопка «Сбросить» удаляет ВСЕ API-ключи (P1 HIGH — НОВЫЙ)
2. **NAV-001** — ссылка «Обновить до Pro →» не реагирует на физический клик (P3, STILL OPEN)
3. **OPENAI-O4MINI** — ошибка max_tokens для моделей серии o* (P3, НОВЫЙ)
4. **GIGACHAT-001** — ошибка биллинга на стороне Сбер GigaChat (НЕ баг приложения)

---

## ИСПРАВЛЕННЫЕ БАГИ (подтверждено ретестом V27)

| Bug ID | Описание | V26 | V27 |
|--------|----------|-----|-----|
| P0-3-CLAUDE | RAW JSON в результатах Claude | ✅ CONFIRMED | ✅ CONFIRMED |
| GROQ-KEY | Ключ Groq не сохраняется | ✅ CONFIRMED | ✅ CONFIRMED |
| AVATAR-001 | Инициалы не соответствуют имени | ✅ CONFIRMED | ✅ CONFIRMED |
| LOGOUT-001 | Нет кнопки выхода | ✅ CONFIRMED | ✅ CONFIRMED |
| DASHBOARD-001 | «Недавние резюме» пустые | ✅ FIXED | ✅ CONFIRMED |
| EMAIL-VERIFY-001 | Противоречие баннера верификации | 🔵 NEW | ✅ FIXED |

---

## 🔴 ДЕФЕКТ 1: RESET-001 — «Сбросить» удаляет ВСЕ API-ключи (P1 HIGH)

**Severity:** P1 — Потеря пользовательских данных
**Страница:** /app/settings/ai — секция «Параметры оптимизации»
**Воспроизводимость:** 100%

### Описание

Кнопка «Сбросить» в настройках AI-моделей при нажатии:
- ✅ Корректно сбрасывает тогглы к дефолтам (Метрики ON, ATS ON, Апгрейд OFF, Язык ON, Soft skills OFF)
- ❌ **УДАЛЯЕТ ВСЕ API-ключи всех 5 провайдеров** (GigaChat, OpenAI, Anthropic, OpenRouter, Groq)
- После перезагрузки страницы все провайдеры показывают ⚠️ вместо ✅
- Ключи удалены на сервере (не только из UI)

### Шаги воспроизведения
1. Войти в аккаунт
2. Перейти в Настройки → AI-модели
3. Убедиться что все 5 API-ключей настроены (все показывают «✓ Сохранён»)
4. Нажать кнопку «Сбросить»
5. Наблюдать: все зелёные «✓ Сохранён» пропадают
6. Перезагрузить страницу
7. Результат: все 5 провайдеров показывают ⚠️, ключи потеряны

### Ожидаемое поведение
«Сбросить» должна сбрасывать ТОЛЬКО:
- 5 тогглов параметров оптимизации к значениям по умолчанию
- Выбранную AI-модель к модели по умолчанию

**НЕ должна затрагивать:**
- Сохранённые API-ключи провайдеров

### Исправление

#### Backend: endpoint сброса настроек

Проблема скорее всего в backend endpoint, который обрабатывает сброс. Нужно разделить сброс тогглов и ключей.

```python
# Файл: app/api/v1/settings.py (или аналогичный)

# БЫЛО (вероятно) — сбрасывает ВСЕ настройки AI:
@router.post("/settings/ai-reset")
async def reset_ai_settings(user_id: str):
    # Удаляет ВСЕ: тогглы + модель + ключи
    await db.settings.delete_many({"user_id": user_id, "category": "ai"})
    return {"status": "ok"}

# ДОЛЖНО БЫТЬ — сбрасывает ТОЛЬКО тогглы и модель:
@router.post("/settings/ai-reset")
async def reset_ai_settings(user_id: str):
    # Сброс ТОЛЬКО тогглов к дефолтам
    defaults = {
        "auto_metrics": True,
        "ats_optimization": True,
        "upgrade_position": False,
        "keep_language": True,
        "soft_skills": False
    }
    await db.settings.update_one(
        {"user_id": user_id},
        {"$set": {"ai_toggles": defaults}},
        upsert=True
    )
    # Сброс модели к дефолту (если нужно)
    await db.settings.update_one(
        {"user_id": user_id},
        {"$set": {"ai_model": "default_model"}},
        upsert=True
    )
    # API-ключи НЕ трогаем!
    return {"status": "ok"}
```

#### Frontend: убедиться что «Сбросить» не очищает поля ключей

```typescript
// Файл: src/pages/Settings/AISettings.tsx (или аналогичный)

const handleReset = async () => {
    // Сбросить ТОЛЬКО тогглы к дефолтам
    setToggles({
        autoMetrics: true,
        atsOptimization: true,
        upgradePosition: false,
        keepLanguage: true,
        softSkills: false,
    });

    // Сбросить выбранную модель к дефолту
    setSelectedModel(DEFAULT_MODEL);

    // НЕ трогать apiKeys!
    // НЕ вызывать setApiKeys({}) или аналогичное

    // Отправить на сервер ТОЛЬКО тогглы и модель
    await api.put('/settings/ai-toggles', { toggles: defaultToggles });
    await api.put('/settings/ai-model', { model: DEFAULT_MODEL });
    // НЕ отправлять запрос на удаление ключей!
};
```

---

## ⚠️ ДЕФЕКТ 2: NAV-001 — «Обновить до Pro →» не кликается (P3 LOW)

**Severity:** P3 (Low)
**Страница:** Sidebar на всех страницах /app/*
**Статус:** STILL OPEN (с V25)

### Описание
Ссылка «Обновить до Pro →» в нижней части sidebar:
- DOM корректный: `<a class="plan-upgrade" href="/app/settings/subscription">`
- Физический клик мышью НЕ вызывает навигацию
- Программный `element.click()` через JS — работает
- **Workaround есть:** пользователь может перейти через Настройки → Подписка

### Вероятная причина
1. CSS overlay или pseudo-element перекрывает ссылку
2. Родительский контейнер sidebar перехватывает клик (preventDefault)
3. Z-index конфликт

### Исправление

```css
/* Файл: src/components/Sidebar.css (или styled-components) */

/* Убедиться что план-виджет кликабелен */
.sidebar-plan-widget,
.plan-info-container {
    position: relative;
    z-index: 10;
}

.plan-upgrade {
    position: relative;
    z-index: 11;
    pointer-events: auto !important;
    cursor: pointer;
    display: inline-block;
}

/* Проверить что нет overlay поверх sidebar */
.sidebar::after,
.sidebar::before,
.sidebar-content::after {
    pointer-events: none !important;
}
```

```tsx
// Файл: src/components/Sidebar.tsx

// Убедиться что Link/NavLink используется корректно:
// Если используется <a> с onClick:
<a
    href="/app/settings/subscription"
    className="plan-upgrade"
    onClick={(e) => {
        // НЕ вызывать e.preventDefault() здесь!
        // Или если нужен React Router:
        e.preventDefault();
        navigate('/app/settings/subscription');
    }}
>
    Обновить до Pro →
</a>

// ЛУЧШЕ: использовать React Router Link:
<Link to="/app/settings/subscription" className="plan-upgrade">
    Обновить до Pro →
</Link>
```

---

## ⚠️ ДЕФЕКТ 3: OPENAI-O4MINI — Ошибка max_tokens для o4-mini (P3 LOW)

**Severity:** P3 (Low)
**Страница:** Оптимизация резюме с моделью o4-mini

### Описание
При оптимизации с моделью openai:o4-mini API возвращает:
```
400 Bad Request: "max_tokens" is an unsupported parameter for this model
```

Модели серии OpenAI o* (o1, o1-mini, o3, o3-mini, o4-mini) используют параметр `max_completion_tokens` вместо `max_tokens`.

### Исправление

```python
# Файл: app/services/llm/openai_provider.py (или аналогичный)

def build_request_params(model: str, prompt: str, max_tokens: int) -> dict:
    params = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    # Модели серии o* используют max_completion_tokens
    if model.startswith("o") and model[1:2].isdigit():
        # o1, o1-mini, o3, o3-mini, o4-mini и т.д.
        params["max_completion_tokens"] = max_tokens
    else:
        # gpt-4o, gpt-4o-mini, gpt-3.5-turbo и т.д.
        params["max_tokens"] = max_tokens

    return params
```

Альтернативный подход — список моделей:
```python
O_SERIES_MODELS = {"o1", "o1-mini", "o1-pro", "o3", "o3-mini", "o4-mini"}

def get_token_param_name(model: str) -> str:
    model_base = model.split("-2024")[0].split("-2025")[0]  # убрать дату
    if model_base in O_SERIES_MODELS:
        return "max_completion_tokens"
    return "max_tokens"
```

---

## РЕЗЮМЕ ДЕЙСТВИЙ

### Приоритет 1 (КРИТИЧНЫЙ):
- [ ] **RESET-001**: Исправить кнопку «Сбросить» — сбрасывать только тогглы и модель, НЕ удалять API-ключи

### Приоритет 2 (СРЕДНИЙ):
- [ ] **OPENAI-O4MINI**: Использовать `max_completion_tokens` для моделей серии o*

### Приоритет 3 (НИЗКИЙ):
- [ ] **NAV-001**: Исправить клик на «Обновить до Pro →» в sidebar

### Не баг приложения:
- **GIGACHAT-001**: 402 Payment Required — проблема биллинга на стороне Сбер. Рекомендация: показать пользователю понятное сообщение «Ошибка биллинга GigaChat — проверьте баланс в личном кабинете Сбер» вместо raw ошибки.

---

## СТАТИСТИКА КАЧЕСТВА

| Метрика | Значение |
|---------|----------|
| Всего багов найдено (V1-V27) | 10 |
| Исправлено и подтверждено | 6 |
| Открытых багов приложения | 3 (RESET-001, NAV-001, OPENAI-O4MINI) |
| Provider-side | 1 (GIGACHAT-001) |
| Критичных (P1) | 1 (RESET-001) |
| Оценка V27 | 8.5/10 |
| Production ready | ✅ ДА (после фикса RESET-001) |
