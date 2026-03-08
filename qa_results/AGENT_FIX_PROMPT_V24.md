# AGENT FIX PROMPT V24 — Оставшиеся баги + Документация + Тесты

> **Контекст:** QA Report #19 — полный ретест. 10 из 12 багов V23 исправлены. Осталось 6 багов (3 серьёзных + 3 минорных).
> **Дата:** 2026-03-08

---

## ДЕФЕКТ 1 (P0): RAW JSON в результатах Anthropic Claude — P0-3-CLAUDE

**Проблема:** При оптимизации через провайдер Anthropic Claude (claude-sonnet-4-6) на ResultsPage секция "Оптимизированное резюме" отображает RAW JSON с markdown code blocks вместо отформатированного текста. OpenAI и OpenRouter отображают результат корректно.

**Текущее поведение:**
```
Пользователь видит:
```json
{"name": "Иванов Пётр", "position": "Golang Developer", ...}
```
```

**Ожидаемое поведение:**
```
Пользователь видит:
Иванов Пётр
Golang Developer
...форматированный текст резюме...
```

**Как исправить:**

```typescript
// Файл: ResultsPage.tsx или компонент OptimizedResumeView

// Проблема: Anthropic Claude возвращает ответ в формате:
// ```json\n{...}\n```
// или
// {"name": "...", "position": "..."}
//
// Frontend не парсит этот JSON для данного провайдера.

// Решение — универсальный парсер ответа:
function parseOptimizedResume(rawText: string, provider: string): ResumeData {
  let text = rawText;

  // 1. Убрать markdown code blocks
  text = text.replace(/^```(?:json)?\s*\n?/gm, '');
  text = text.replace(/\n?```\s*$/gm, '');
  text = text.trim();

  // 2. Попробовать распарсить как JSON
  try {
    const parsed = JSON.parse(text);
    if (typeof parsed === 'object' && parsed !== null) {
      return formatResumeFromJSON(parsed);
    }
  } catch (e) {
    // Не JSON — значит уже текст, вернуть как есть
  }

  // 3. Вернуть как plain text
  return { rawText: text };
}

// Применять ОДИНАКОВО для всех провайдеров,
// не только OpenAI/OpenRouter.
```

**Тестирование:**
- Оптимизировать резюме через Claude claude-sonnet-4-6
- На ResultsPage проверить: текст отформатирован, нет ```json, нет raw JSON
- Секция опыта: bullet points, не [object Object]

---

## ДЕФЕКТ 2 (P2): GigaChat Pro — ошибка биллинга — GIGACHAT-001

**Проблема:** GigaChat-Pro возвращает ошибку "Недостаточно средств на балансе провайдера" при попытке оптимизации. Все 3 из 4 этапов проходят, ошибка на финальном.

**Как исправить:**

```python
# 1. Проверить API-ключ GigaChat:
#    - Зайти на https://developers.sber.ru/
#    - Проверить баланс аккаунта
#    - Убедиться что ключ активен и не истёк
#    - При необходимости пополнить баланс или сгенерировать новый ключ

# 2. Добавить health-check при старте сервера:
async def check_provider_health(provider: str) -> dict:
    """Проверяет доступность и баланс провайдера."""
    try:
        if provider == "gigachat":
            # Отправить минимальный запрос для проверки
            response = await gigachat_client.chat(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return {"status": "ok", "provider": provider}
    except BillingError:
        return {"status": "billing_error", "provider": provider,
                "message": "Недостаточно средств"}
    except AuthError:
        return {"status": "auth_error", "provider": provider,
                "message": "Невалидный API-ключ"}
    except Exception as e:
        return {"status": "error", "provider": provider,
                "message": str(e)}

# 3. Эндпоинт для проверки статуса провайдеров:
@router.get("/api/providers/status")
async def get_providers_status():
    """Возвращает статус каждого провайдера."""
    results = {}
    for provider in PROVIDERS:
        results[provider] = await check_provider_health(provider)
    return results

# 4. Frontend: вызывать /api/providers/status при загрузке /app/models
#    Помечать недоступные провайдеры как "Недоступен" с причиной
```

---

## ДЕФЕКТ 3 (P2): API-ключ Groq не сохраняется — GROQ-KEY

**Проблема:** На странице /app/settings/ai ключ Groq вводится в поле (отображается "gsk_..."), но не сохраняется. После обновления страницы — ключ пропал. Groq в /app/models показывает "Нет ключа".

**Как исправить:**

```typescript
// Файл: компонент настроек AI-моделей (AISettingsPage.tsx или подобный)

// 1. Проверить что Groq включён в список провайдеров для сохранения ключей:
const PROVIDER_KEY_FIELDS = {
  gigachat: 'gigachat_api_key',
  openai: 'openai_api_key',
  anthropic: 'anthropic_api_key',
  openrouter: 'openrouter_api_key',
  groq: 'groq_api_key',  // ← Проверить наличие!
};

// 2. Backend: проверить что эндпоинт POST /api/settings/api-keys
//    принимает и сохраняет groq_api_key:
@router.post("/api/settings/api-keys")
async def save_api_keys(keys: APIKeysSchema):
    # Проверить что groq_api_key есть в схеме
    # Проверить что сохраняется в БД (users table или settings table)
    pass

// 3. После сохранения — отображать "✓ Сохранён" рядом с полем Groq
// 4. На /app/models — убрать бейдж "Нет ключа" если ключ сохранён
```

**Тестирование:**
- Ввести ключ Groq → нажать "Сохранить"
- Обновить страницу → ключ должен отображаться (замаскированный)
- На /app/models → Groq без бейджа "Нет ключа"
- Запустить оптимизацию с Groq → должна работать

---

## ДЕФЕКТ 4 (P3): Несоответствие инициалов аватара — AVATAR-001

**Проблема:** Аватар в профиле показывает "АП" (первые буквы фамилии?), а в сайдбаре "QT" (первые буквы имени на латинице). Для пользователя "QA Tester March".

**Как исправить:**

```typescript
// Унифицировать генерацию инициалов:
function getInitials(firstName: string, lastName: string): string {
  const first = (firstName || '').trim().charAt(0).toUpperCase();
  const last = (lastName || '').trim().charAt(0).toUpperCase();
  return `${first}${last}` || '??';
}

// Использовать ОДНУ функцию и в Sidebar, и в Profile.
// Текущая проблема: разные компоненты используют разную логику
// (один берёт из латинского имени "QT", другой из русского "АП")
```

---

## ДЕФЕКТ 5 (P3): Нет страницы выхода из аккаунта — LOGOUT-001

**Проблема:** /logout возвращает 404. Нет видимого способа выйти из аккаунта через UI.

**Как исправить:**

```typescript
// 1. Добавить кнопку "Выйти" в сайдбар (рядом с именем пользователя):
<Button onClick={handleLogout} variant="ghost" size="sm">
  <LogOutIcon /> Выйти
</Button>

// 2. Функция выхода:
async function handleLogout() {
  try {
    await fetch('/api/auth/logout', { method: 'POST' });
  } catch (e) {
    // Fallback: очистить токены локально
  }
  localStorage.removeItem('token');
  sessionStorage.clear();
  window.location.href = '/auth';
}

// 3. Backend: POST /api/auth/logout → инвалидировать токен/сессию
```

---

## ДЕФЕКТ 6 (P3): Нестабильная навигация по ссылке "Обновить до Pro" — NAV-001

**Проблема:** Ссылка "Обновить до Pro →" в сайдбаре имеет корректный href (/app/settings/subscription), но клик иногда не приводит к навигации.

**Как исправить:**

```typescript
// Проверить что ссылка использует React Router Link, а не <a>:
// Неправильно:
<a href="/app/settings/subscription">Обновить до Pro →</a>

// Правильно:
<Link to="/app/settings/subscription">Обновить до Pro →</Link>

// Или если используется Next.js:
<Link href="/app/settings/subscription">Обновить до Pro →</Link>

// Также проверить z-index и overflow:
// возможно элемент перекрыт другим слоем
```

---

## ПРИОРИТЕТЫ ИСПРАВЛЕНИЯ

| Приоритет | Дефекты | Описание |
|-----------|---------|----------|
| 🔴 CRITICAL | P0-3-CLAUDE | RAW JSON в результатах Claude — единственный P0 |
| 🟡 MEDIUM | GIGACHAT-001, GROQ-KEY | Провайдеры не работают (billing + key save) |
| 🟢 LOW | AVATAR-001, LOGOUT-001, NAV-001 | Минорный UX |

---

## ОБНОВЛЕНИЕ ДОКУМЕНТАЦИИ

### Changelog (CHANGELOG.md)

Добавить запись:

```markdown
## [v1.3.0] — 2026-03-08

### Исправлено
- **Тарифная система:** Деактивированы кнопки смены плана до интеграции Робокассы.
  Добавлен баннер "Платные тарифы скоро". Страница подписки перенесена в Настройки.
- **ATS Score:** Исправлен маппинг оценок (D = "Плохо", ранее отображалось "Отлично")
- **Match Score:** Компоненты теперь рассчитываются независимо (ранее все показывали одинаковый %)
- **Сайдбар:** Счётчик оптимизаций и название плана обновляются в реальном времени
- **Лимит оптимизаций:** Предупреждение о лимите показывается на первом шаге wizard (Upload),
  а не на последнем
- **Groq:** Добавлен в список провайдеров с бейджами "Новое" и "Быстрый"
- **Экспорт:** Добавлены форматы PDF и TXT (ранее только DOCX)
- **Провайдер по умолчанию:** GigaChat Pro остаётся "Рекомендуем" после ошибок
- **Ошибки провайдеров:** Улучшены сообщения (конкретная причина вместо общей)

### Известные проблемы
- Результаты Anthropic Claude могут отображаться как RAW JSON
- GigaChat Pro: ошибка биллинга на стороне провайдера (требуется пополнение)
- API-ключ Groq не сохраняется в настройках
- Отсутствует функция выхода из аккаунта (/logout)
```

### README обновления

Добавить в секцию "Провайдеры":
```markdown
## Поддерживаемые провайдеры

| Провайдер | Модели | Статус |
|-----------|--------|--------|
| GigaChat Pro (Сбер) | GigaChat-Pro | Рекомендуемый (требует активный баланс) |
| OpenAI | o4-mini, gpt-4o, gpt-4o-mini | Работает |
| Anthropic Claude | claude-sonnet-4-6, claude-haiku-4-5 | Работает (известная проблема с форматированием) |
| OpenRouter | ai21/jamba-large-1.7, llama-3.3-70b, gemini-2.0-flash | Работает |
| Groq | — | Добавлен (требует настройку ключа) |
```

### API документация

Добавить/обновить:
```markdown
## Эндпоинты

### Подписка
- GET /api/settings/subscription — текущий план пользователя
- Интеграция Robokassa — в разработке

### Провайдеры
- GET /api/providers/status — статус всех провайдеров (планируется)
- POST /api/settings/api-keys — сохранение API-ключей (включая Groq)

### Аутентификация
- POST /api/auth/login — вход
- POST /api/auth/register — регистрация
- POST /api/auth/logout — выход (ТРЕБУЕТСЯ РЕАЛИЗАЦИЯ)

### Устаревшие URL
- /app/subscription → /app/settings/subscription
- /login → /auth
- /logout → НЕ РЕАЛИЗОВАН
```

---

## ТЕСТЫ СО 100% ПОКРЫТИЕМ

### 1. Тесты парсинга ответов провайдеров (P0-3-CLAUDE)

```typescript
// __tests__/parseOptimizedResume.test.ts

describe('parseOptimizedResume', () => {
  // Тест 1: Ответ OpenAI (чистый JSON)
  test('parses clean JSON from OpenAI', () => {
    const input = '{"name": "Иванов Пётр", "position": "Developer"}';
    const result = parseOptimizedResume(input, 'openai');
    expect(result.name).toBe('Иванов Пётр');
    expect(result.position).toBe('Developer');
  });

  // Тест 2: Ответ Claude (JSON в markdown code block)
  test('parses JSON wrapped in markdown code blocks from Claude', () => {
    const input = '```json\n{"name": "Иванов", "position": "Dev"}\n```';
    const result = parseOptimizedResume(input, 'anthropic');
    expect(result.name).toBe('Иванов');
    expect(result.position).toBe('Dev');
  });

  // Тест 3: Ответ Claude (JSON без code block)
  test('parses raw JSON from Claude without code blocks', () => {
    const input = '{"name": "Иванов", "experience": [{"company": "Foo"}]}';
    const result = parseOptimizedResume(input, 'anthropic');
    expect(result.experience).toHaveLength(1);
    expect(result.experience[0].company).toBe('Foo');
  });

  // Тест 4: Ответ OpenRouter (plain text)
  test('handles plain text from OpenRouter', () => {
    const input = 'Иванов Пётр\nGolang Developer\n\nОпыт работы...';
    const result = parseOptimizedResume(input, 'openrouter');
    expect(result.rawText).toContain('Иванов Пётр');
  });

  // Тест 5: Ответ с тройными backticks без json
  test('parses code block without json language marker', () => {
    const input = '```\n{"name": "Test"}\n```';
    const result = parseOptimizedResume(input, 'anthropic');
    expect(result.name).toBe('Test');
  });

  // Тест 6: Невалидный JSON
  test('handles malformed JSON gracefully', () => {
    const input = '{"name": "broken';
    const result = parseOptimizedResume(input, 'anthropic');
    expect(result.rawText).toBe('{"name": "broken');
  });

  // Тест 7: Пустая строка
  test('handles empty string', () => {
    const result = parseOptimizedResume('', 'openai');
    expect(result.rawText).toBe('');
  });

  // Тест 8: experience содержит объекты (не [object Object])
  test('experience items are rendered as strings, not [object Object]', () => {
    const input = JSON.stringify({
      name: 'Test',
      experience: [
        { company: 'Foo', role: 'Dev', description: 'Did stuff' }
      ]
    });
    const result = parseOptimizedResume(input, 'openai');
    const rendered = renderExperience(result.experience);
    expect(rendered).not.toContain('[object Object]');
    expect(rendered).toContain('Foo');
  });
});
```

### 2. Тесты ATS Score маппинга

```typescript
// __tests__/atsScoreMapping.test.ts

describe('ATS Grade Mapping', () => {
  test('A maps to "Отлично"', () => {
    expect(getATSLabel('A')).toBe('Отлично');
    expect(getATSColor('A')).toBe('green');
  });

  test('B maps to "Хорошо"', () => {
    expect(getATSLabel('B')).toBe('Хорошо');
    expect(getATSColor('B')).toBe('blue');
  });

  test('C maps to "Средне"', () => {
    expect(getATSLabel('C')).toBe('Средне');
    expect(getATSColor('C')).toBe('yellow');
  });

  test('D maps to "Плохо"', () => {
    expect(getATSLabel('D')).toBe('Плохо');
    expect(getATSColor('D')).toBe('orange');
  });

  test('F maps to "Критично"', () => {
    expect(getATSLabel('F')).toBe('Критично');
    expect(getATSColor('F')).toBe('red');
  });

  test('unknown grade returns "Неизвестно"', () => {
    expect(getATSLabel('Z')).toBe('Неизвестно');
  });
});
```

### 3. Тесты Match Score компонентов

```typescript
// __tests__/matchScore.test.ts

describe('Match Score Components', () => {
  test('each component has independent score', () => {
    const result = calculateMatchScore(resume, vacancy);
    const scores = [
      result.keywords,
      result.experience,
      result.structure,
      result.readability
    ];
    // Крайне маловероятно что все 4 одинаковые
    const unique = new Set(scores);
    expect(unique.size).toBeGreaterThan(1);
  });

  test('weights sum to 100%', () => {
    const weights = {
      keywords: 0.40,
      experience: 0.25,
      structure: 0.20,
      readability: 0.15
    };
    const sum = Object.values(weights).reduce((a, b) => a + b, 0);
    expect(sum).toBeCloseTo(1.0);
  });

  test('overall score equals weighted sum', () => {
    const scores = { keywords: 50, experience: 60, structure: 70, readability: 80 };
    const weights = { keywords: 0.40, experience: 0.25, structure: 0.20, readability: 0.15 };
    const expected = 50*0.40 + 60*0.25 + 70*0.20 + 80*0.15;
    const result = calculateOverallScore(scores, weights);
    expect(result).toBeCloseTo(expected);
  });

  test('scores are between 0 and 100', () => {
    const result = calculateMatchScore(resume, vacancy);
    expect(result.keywords).toBeGreaterThanOrEqual(0);
    expect(result.keywords).toBeLessThanOrEqual(100);
    expect(result.experience).toBeGreaterThanOrEqual(0);
    expect(result.experience).toBeLessThanOrEqual(100);
  });
});
```

### 4. Тесты лимита оптимизаций

```typescript
// __tests__/optimizationLimit.test.ts

describe('Optimization Limit', () => {
  test('shows banner when limit reached on upload page', () => {
    const user = { optimizations_used: 5, plan_limit: 5, plan: 'free' };
    const { getByText } = render(<UploadPage user={user} />);
    expect(getByText('Лимит оптимизаций исчерпан')).toBeInTheDocument();
  });

  test('shows remaining count when not at limit', () => {
    const user = { optimizations_used: 3, plan_limit: 5, plan: 'free' };
    const { queryByText } = render(<UploadPage user={user} />);
    expect(queryByText('Лимит оптимизаций исчерпан')).toBeNull();
  });

  test('banner includes link to subscription page', () => {
    const user = { optimizations_used: 5, plan_limit: 5, plan: 'free' };
    const { getByText } = render(<UploadPage user={user} />);
    const link = getByText('Посмотреть тарифы');
    expect(link).toHaveAttribute('href', '/app/settings/subscription');
  });

  test('failed optimization does not consume credit', async () => {
    const user = { optimizations_used: 3 };
    await simulateFailedOptimization(user);
    expect(user.optimizations_used).toBe(3);
  });
});
```

### 5. Тесты подписки

```typescript
// __tests__/subscription.test.ts

describe('Subscription Page', () => {
  test('shows "Скоро" buttons for paid plans', () => {
    const { getAllByText } = render(<SubscriptionPage plan="free" />);
    const buttons = getAllByText('Скоро');
    expect(buttons).toHaveLength(2); // Standard и Pro
    buttons.forEach(btn => expect(btn).toBeDisabled());
  });

  test('shows "Текущий план" for active plan', () => {
    const { getByText } = render(<SubscriptionPage plan="free" />);
    expect(getByText('Текущий план')).toBeInTheDocument();
  });

  test('shows Robokassa banner', () => {
    const { getByText } = render(<SubscriptionPage plan="free" />);
    expect(getByText(/Платные тарифы скоро/)).toBeInTheDocument();
  });

  test('displays correct optimization count', () => {
    const { getByText } = render(
      <SubscriptionPage plan="free" used={3} limit={5} />
    );
    expect(getByText(/3 из 5/)).toBeInTheDocument();
  });
});
```

### 6. Тесты API-ключей провайдеров

```typescript
// __tests__/apiKeySettings.test.ts

describe('API Key Settings', () => {
  test('saves Groq API key', async () => {
    const mockSave = jest.fn().mockResolvedValue({ success: true });
    const { getByLabelText, getByText } = render(
      <AISettingsPage onSave={mockSave} />
    );

    fireEvent.change(getByLabelText('Groq API Key'), {
      target: { value: 'gsk_test123' }
    });
    fireEvent.click(getByText('Сохранить'));

    expect(mockSave).toHaveBeenCalledWith(
      expect.objectContaining({ groq_api_key: 'gsk_test123' })
    );
  });

  test('shows checkmark after successful save', async () => {
    // Сохранить ключ → должна появиться метка "✓ Сохранён"
    const { findByText } = render(<AISettingsPage />);
    await saveKey('groq', 'gsk_test123');
    expect(await findByText('✓ Сохранён')).toBeInTheDocument();
  });

  test('all 5 providers have key fields', () => {
    const { container } = render(<AISettingsPage />);
    const keyFields = container.querySelectorAll('[data-provider-key]');
    expect(keyFields).toHaveLength(5);
  });

  test('masks saved API keys', () => {
    const { getByLabelText } = render(
      <AISettingsPage savedKeys={{ openai: 'sk-proj-abc123...' }} />
    );
    const field = getByLabelText('OpenAI API Key');
    expect(field.value).toMatch(/^sk-proj-\.\.\./);
  });
});
```

### 7. Тесты сайдбара

```typescript
// __tests__/sidebar.test.ts

describe('Sidebar', () => {
  test('shows current plan name', () => {
    const { getByText } = render(<Sidebar user={{ plan: 'free' }} />);
    expect(getByText('Бесплатный план')).toBeInTheDocument();
  });

  test('updates optimization count after optimization', async () => {
    const user = { optimizations_used: 3, plan_limit: 5 };
    const { getByText, rerender } = render(<Sidebar user={user} />);
    expect(getByText('3 / 5 оптимизаций')).toBeInTheDocument();

    user.optimizations_used = 4;
    rerender(<Sidebar user={user} />);
    expect(getByText('4 / 5 оптимизаций')).toBeInTheDocument();
  });

  test('shows consistent avatar initials with profile', () => {
    const user = { firstName: 'QA', lastName: 'Tester March' };
    const sidebarInitials = getInitials(user.firstName, user.lastName);
    const profileInitials = getInitials(user.firstName, user.lastName);
    expect(sidebarInitials).toBe(profileInitials);
  });
});
```

### 8. Тесты навигации

```typescript
// __tests__/navigation.test.ts

describe('Navigation', () => {
  test('/app/subscription redirects to /app/settings/subscription', () => {
    // Старый URL должен редиректить или показывать 404 с подсказкой
    const { getByText } = render(<Router initialPath="/app/subscription" />);
    // Либо редирект, либо 404
  });

  test('sidebar "Обновить до Pro" navigates to subscription', () => {
    const { getByText } = render(<Sidebar />);
    const link = getByText('Обновить до Pro →');
    expect(link.closest('a')).toHaveAttribute('href', '/app/settings/subscription');
    fireEvent.click(link);
    expect(window.location.pathname).toBe('/app/settings/subscription');
  });

  test('logout clears session and redirects to /auth', async () => {
    await handleLogout();
    expect(localStorage.getItem('token')).toBeNull();
    expect(window.location.pathname).toBe('/auth');
  });
});
```

### 9. Тесты провайдеров (integration)

```typescript
// __tests__/providers.integration.test.ts

describe('Provider Integration', () => {
  test('failed optimization does not consume credit', async () => {
    const before = await getUserOptimizations();
    await attemptOptimization('gigachat-pro'); // Will fail
    const after = await getUserOptimizations();
    expect(after).toBe(before);
  });

  test('error page shows "Выбрать другую модель" button', () => {
    const { getByText } = render(<ProcessingError error="billing" />);
    expect(getByText('Выбрать другую модель')).toBeInTheDocument();
    expect(getByText('Настроить ключи')).toBeInTheDocument();
  });

  test('Groq appears in provider list with "Нет ключа" badge', () => {
    const { getByText } = render(<ModelsPage providers={providersWithoutGroqKey} />);
    const groq = getByText('Groq');
    expect(groq).toBeInTheDocument();
    expect(getByText('Нет ключа')).toBeInTheDocument();
  });

  test('provider health check marks unhealthy providers', async () => {
    const statuses = await checkProviderHealth();
    if (statuses.gigachat.status !== 'ok') {
      const { getByText } = render(<ModelsPage statuses={statuses} />);
      expect(getByText('Недоступен')).toBeInTheDocument();
    }
  });
});
```

### 10. Тесты error handling

```python
# tests/test_provider_errors.py

class TestProviderErrorHandling:
    def test_billing_error_returns_specific_message(self):
        """Ошибка биллинга должна возвращать конкретное сообщение."""
        error = ProviderBillingError("insufficient_funds")
        message = format_provider_error(error)
        assert "средств" in message.lower() or "баланс" in message.lower()

    def test_auth_error_returns_specific_message(self):
        """Ошибка аутентификации должна возвращать конкретное сообщение."""
        error = ProviderAuthError("invalid_key")
        message = format_provider_error(error)
        assert "аутентификац" in message.lower() or "ключ" in message.lower()

    def test_rate_limit_error_returns_retry_message(self):
        """Ошибка лимита должна предлагать подождать."""
        error = ProviderRateLimitError("rate_limit_exceeded")
        message = format_provider_error(error)
        assert "минут" in message.lower() or "подожд" in message.lower()

    def test_failed_optimization_does_not_decrement_credits(self):
        """Неудачная оптимизация не должна списывать кредит."""
        user = create_test_user(optimizations_used=3)
        with pytest.raises(ProviderError):
            run_optimization(user, provider="gigachat")
        user.refresh_from_db()
        assert user.optimizations_used == 3

    def test_successful_optimization_increments_credits(self):
        """Успешная оптимизация должна списывать кредит."""
        user = create_test_user(optimizations_used=3)
        run_optimization(user, provider="openai")
        user.refresh_from_db()
        assert user.optimizations_used == 4
```

---

## КОНТРОЛЬНЫЙ СПИСОК ПЕРЕД РЕЛИЗОМ

- [ ] Дефект P0-3-CLAUDE исправлен — парсинг ответов Claude
- [ ] Дефект GROQ-KEY исправлен — ключ сохраняется
- [ ] Дефект GIGACHAT-001 — проверен баланс API
- [ ] Дефект AVATAR-001 — единая функция инициалов
- [ ] Дефект LOGOUT-001 — кнопка выхода в сайдбаре
- [ ] Дефект NAV-001 — ссылка Pro использует React Router
- [ ] CHANGELOG.md обновлён
- [ ] README.md обновлён (секция провайдеров)
- [ ] API документация обновлена
- [ ] Все тесты из секции выше написаны и проходят
- [ ] Покрытие тестами ≥ 100% для изменённых файлов
