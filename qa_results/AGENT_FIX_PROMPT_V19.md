# AGENT FIX PROMPT V19 — Оставшиеся дефекты после ретеста V18

**Дата:** 2026-03-07
**Источник:** QA Report #14 (14_RETEST_V18_FINAL.md)
**Дефектов к исправлению:** 5 (2 критичных, 1 высокий, 1 средний, 1 низкий)

---

## 🔴 P0-3 — CRITICAL: RAW JSON в результатах оптимизации

**Проблема:** Страница `/app/results` отображает сырой JSON в колонке «Оптимизировано» вместо форматированного текста резюме.

**Что видит пользователь:**
```
"json { "summary": "Senior PHP Developer с 14-летним опытом...", "experience": [{"position": "...", "company": "...", "achievements": [...]}]}"
```

**Ожидание:** Форматированный текст с секциями (Резюме, Опыт работы, Образование, Навыки), bullet points для достижений.

**Где исправлять:**
- Frontend: компонент результатов оптимизации (вероятно `ResultsPage.tsx` или `OptimizedResumeView.tsx`)
- Нужно: при получении данных из API проверять, является ли поле `optimized_text` строкой с JSON-структурой, парсить и рендерить в читаемый формат

**Алгоритм исправления:**
1. Получить `optimized_text` из API response
2. Если строка начинается с `"json {` или `{` — распарсить JSON
3. Из JSON извлечь секции (summary, experience, education, skills)
4. Отрендерить каждую секцию с заголовками и форматированием
5. Если не JSON — показать как plain text с Markdown-рендерингом

---

## 🔴 P0-4 — CRITICAL: OpenAI o-series max_tokens ошибка

**Проблема:** Модели OpenAI o-серии (o1, o3-mini, o4-mini) возвращают ошибку:
```
Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.
```

**Где исправлять:**
- Backend: сервис вызова LLM (вероятно `llm_service.py` или `openai_provider.py`)
- В месте формирования запроса к OpenAI API

**Алгоритм исправления:**
1. Определить, является ли модель o-серией: проверить `model_name.startswith("o1") or model_name.startswith("o3") or model_name.startswith("o4")`
2. Для o-серии: использовать параметр `max_completion_tokens` вместо `max_tokens`
3. Для остальных моделей OpenAI (gpt-4o, gpt-4o-mini и т.д.): оставить `max_tokens`

```python
# Пример исправления:
if model_name.startswith(("o1", "o3", "o4")):
    params["max_completion_tokens"] = max_tokens
else:
    params["max_tokens"] = max_tokens
```

---

## 🟠 NEW-V18-001 — HIGH: Resume file API → 500 Internal Server Error

**Проблема:** `GET /api/v1/resumes/{id}/file` возвращает 500.

**Где исправлять:**
- Backend: эндпоинт получения файла резюме
- Проверить: существует ли файл на диске/в S3, корректен ли путь к файлу в БД

**Возможные причины:**
1. Файл не существует по указанному пути (удалён или не загружен)
2. Ошибка чтения файла (permissions, отсутствие директории)
3. Некорректный Content-Type или кодировка

**Алгоритм исправления:**
1. Добавить try/except в endpoint
2. Проверить наличие файла перед чтением
3. Вернуть 404 если файл не найден, а не 500
4. Логировать ошибку с полным traceback

---

## 🟡 NEW-V18-002 — MEDIUM: Прогресс-бар застревает на 0%

**Проблема:** Страница `/app/processing` показывает 0% в течение ~23 секунд, затем перескакивает на 100%.

**Где исправлять:**
- Frontend: компонент ProcessingPage
- Polling механизм для `/api/v1/rewrite/{id}/status`

**Алгоритм исправления:**
1. Уменьшить polling interval с текущего значения до 2-3 секунд
2. Убедиться, что response.progress корректно маппится на UI прогресс-бар
3. Альтернатива: реализовать SSE (Server-Sent Events) для realtime обновлений
4. Добавить анимацию «пульс» пока прогресс 0% для индикации активности

---

## 🟢 P3-1 — LOW: OpenRouter dropdown без группировки

**Проблема:** 300+ моделей в плоском списке без визуальных разделителей по провайдерам.

**Текущее состояние:** Модели отсортированы по провайдеру, есть поиск. Но нет `<optgroup>` заголовков.

**Где исправлять:**
- Frontend: компонент выбора модели OpenRouter

**Алгоритм исправления:**
1. Сгруппировать модели по provider prefix (часть до `:` или `/`)
2. Использовать `<optgroup label="Anthropic">`, `<optgroup label="Google">` и т.д.
3. Или: использовать кастомный select с визуальными заголовками секций

---

## Итого: 5 дефектов

| Приоритет | ID | Описание |
|-----------|-----|----------|
| 🔴 P0 | P0-3 | RAW JSON в результатах |
| 🔴 P0 | P0-4 | OpenAI o-series max_tokens |
| 🟠 P1 | NEW-V18-001 | Resume file 500 |
| 🟡 P2 | NEW-V18-002 | Прогресс-бар 0% |
| 🟢 P3 | P3-1 | OpenRouter dropdown |
