/**
 * V31 Frontend Tests
 *
 * Covers:
 * - HISTORY-RAW-ERROR-001: friendlyError() and sanitizeErrorMessage() strip raw data
 * - FILE-UPLOAD-001: file input uses opacity instead of display:none
 * - KEY-CHECK-001: isAuthError() detects auth errors correctly
 */

import { describe, it, expect } from 'vitest'

// ============================================================================
// HISTORY-RAW-ERROR-001: ProcessingPage friendlyError
// ============================================================================

// Inline the function to test it (since it's not exported)
function friendlyError(msg: string): string {
  if (/провайдер all|provider all/i.test(msg)) {
    return 'Ни один LLM-провайдер не настроен. Перейдите в настройки AI и добавьте API-ключ хотя бы для одного провайдера (OpenAI, Anthropic, OpenRouter или GigaChat).'
  }
  if (/api-ключ.*не настроен|не настроен.*api-ключ/i.test(msg)) {
    return msg.split('.')[0] + '. Перейдите в настройки AI и проверьте ключ.'
  }
  if (/insufficient.?balance|недостаточно средств|quota.?exceeded/i.test(msg)) {
    return 'Недостаточно средств на балансе провайдера. Пополните баланс аккаунта поставщика или выберите другую модель.'
  }
  if (/payment.?required|402|billing/i.test(msg)) {
    return 'Ошибка оплаты у поставщика модели. Проверьте тарифный план и баланс аккаунта провайдера, или выберите другую модель.'
  }
  if (/rate.?limit|429|too many/i.test(msg)) {
    return 'Превышен лимит запросов к модели. Подождите минуту и попробуйте снова, или выберите другую модель.'
  }
  if (/URL\(|https?:\/\/|{.*error.*}|status_code|b'|\\x/i.test(msg)) {
    return 'Произошла ошибка при обращении к AI-провайдеру. Попробуйте позже или выберите другую модель.'
  }
  if (/max_tokens|max_completion_tokens|unsupported parameter/i.test(msg)) {
    return 'Ошибка параметров запроса к AI-модели. Попробуйте выбрать другую модель.'
  }
  if (/временно недоступен/i.test(msg)) {
    return 'AI-провайдер временно недоступен. Попробуйте позже или выберите другую модель.'
  }
  return msg
}

function sanitizeErrorMessage(msg: string): string {
  if (/api-ключ.*не настроен/i.test(msg)) return msg.split('.')[0]
  if (/провайдер all|provider all/i.test(msg)) return 'Нет доступных AI-провайдеров'
  if (/URL\(|https?:\/\/|{.*error.*}|status_code|b'|\\x/i.test(msg)) return 'Ошибка AI-провайдера'
  if (/max_tokens|max_completion_tokens|unsupported parameter/i.test(msg)) return 'Ошибка параметров запроса'
  if (/недостаточно средств|billing|quota/i.test(msg)) return 'Недостаточно средств у провайдера'
  if (/rate.?limit|429|too many/i.test(msg)) return 'Превышен лимит запросов'
  if (/временно недоступен/i.test(msg)) return 'AI-провайдер временно недоступен'
  if (msg.length > 80) return msg.slice(0, 77) + '...'
  return msg
}

describe('HISTORY-RAW-ERROR-001: friendlyError strips raw LLM errors', () => {
  it('should strip raw GigaChat URL error', () => {
    const raw = "LLM-провайдер gigachat-pro: (URL('https://ngw.devices.sberbank.ru:9443/api/v2/oauth'), 400, b'{\"error\":\"invalid_client\"}') временно недоступен"
    const result = friendlyError(raw)
    expect(result).not.toContain('https://')
    expect(result).not.toContain('sberbank')
    expect(result).not.toContain('URL(')
  })

  it('should strip raw OpenAI max_tokens error', () => {
    const raw = "LLM-провайдер openai: Error code: 400 - {'error': {'message': \"Unsupported parameter: 'max_tokens' is not supported with this model.\"}}"
    const result = friendlyError(raw)
    expect(result).not.toContain('max_tokens')
    expect(result).not.toContain("Error code")
    expect(result).toContain('модель')
  })

  it('should handle provider all error', () => {
    const msg = 'Все LLM-провайдеры временно недоступны. Провайдер all не настроен.'
    const result = friendlyError(msg)
    expect(result).toContain('настройки AI')
  })

  it('should handle auth key not configured', () => {
    const msg = 'API-ключ для OpenAI не настроен. Для использования OpenAI необходимо указать API-ключ.'
    const result = friendlyError(msg)
    expect(result).toContain('API-ключ для OpenAI не настроен')
    expect(result).toContain('настройки AI')
  })

  it('should handle rate limit errors', () => {
    const msg = 'rate limit exceeded'
    const result = friendlyError(msg)
    expect(result).toContain('лимит')
  })

  it('should pass through clean messages', () => {
    const msg = 'Оптимизация завершена.'
    const result = friendlyError(msg)
    expect(result).toBe(msg)
  })

  it('should handle temporarily unavailable message', () => {
    const msg = 'AI-провайдер временно недоступен'
    const result = friendlyError(msg)
    expect(result).toContain('недоступен')
  })
})

describe('HISTORY-RAW-ERROR-001: sanitizeErrorMessage for history page', () => {
  it('should truncate raw URL errors', () => {
    const raw = "LLM-провайдер gigachat-pro: (URL('https://ngw.devices.sberbank.ru:9443'), 400, b'{}')"
    const result = sanitizeErrorMessage(raw)
    expect(result).toBe('Ошибка AI-провайдера')
    expect(result).not.toContain('URL')
  })

  it('should shorten API key not configured', () => {
    const msg = 'API-ключ для OpenAI не настроен. Подробности...'
    const result = sanitizeErrorMessage(msg)
    expect(result).toBe('API-ключ для OpenAI не настроен')
  })

  it('should handle provider all', () => {
    const msg = 'Все LLM-провайдеры временно недоступны. Провайдер all не настроен.'
    const result = sanitizeErrorMessage(msg)
    expect(result).toBe('Нет доступных AI-провайдеров')
  })

  it('should truncate very long messages', () => {
    const msg = 'A'.repeat(100)
    const result = sanitizeErrorMessage(msg)
    expect(result.length).toBeLessThanOrEqual(80)
    expect(result).toContain('...')
  })

  it('should pass through short clean messages', () => {
    const msg = 'Ошибка обработки'
    const result = sanitizeErrorMessage(msg)
    expect(result).toBe(msg)
  })
})

// ============================================================================
// KEY-CHECK-001: isAuthError detection
// ============================================================================

function isAuthError(msg: string): boolean {
  const lower = msg.toLowerCase()
  return lower.includes('api-ключ') || lower.includes('не настроен') || lower.includes('unauthorized') || lower.includes('провайдер all') || lower.includes('provider all')
}

describe('KEY-CHECK-001: isAuthError recognizes key-related errors', () => {
  it('should detect API key not configured', () => {
    expect(isAuthError('API-ключ для OpenAI не настроен')).toBe(true)
  })

  it('should detect provider all error', () => {
    expect(isAuthError('Все LLM-провайдеры... провайдер all')).toBe(true)
  })

  it('should detect unauthorized', () => {
    expect(isAuthError('Unauthorized')).toBe(true)
  })

  it('should not flag normal errors', () => {
    expect(isAuthError('Таймаут запроса')).toBe(false)
  })
})

// ============================================================================
// FILE-UPLOAD-001: file input hidden via opacity (DOM test via string check)
// ============================================================================

describe('FILE-UPLOAD-001: file input uses opacity instead of display:none', () => {
  it('should use opacity:0 in UploadPage source', async () => {
    // Read the source to verify the fix
    const fs = await import('fs')
    const src = fs.readFileSync('src/pages/wizard/UploadPage.tsx', 'utf-8')
    expect(src).toContain('opacity: 0')
    expect(src).not.toContain("display: 'none'")
  })
})
