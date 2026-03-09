/**
 * Tests for V30 fixes:
 * 1. FILE-UPLOAD-001: uploadResume() auth fallback, 401 retry, error parsing (P3 LOW)
 * 2. SCORE-VARIANCE-001: documented as expected behaviour (P4 INFO — no code fix)
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ─── FILE-UPLOAD-001: uploadResume auth/retry/error logic ────────────

describe('FILE-UPLOAD-001: uploadResume auth, retry, error parsing', () => {
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('sends Authorization header from localStorage when this.token is null', async () => {
    localStorage.setItem('access_token', 'ls-token-123')
    localStorage.setItem('refresh_token', 'rt-456')

    const fetchCalls: RequestInit[] = []
    globalThis.fetch = vi.fn(async (_url: string | URL | Request, init?: RequestInit) => {
      fetchCalls.push(init || {})
      return new Response(JSON.stringify({ id: 'r1', status: 'draft' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }) as unknown as typeof fetch

    // Re-import ApiClient to get a fresh instance
    vi.resetModules()
    const { ApiClient } = await import('../services/api')
    const client = new ApiClient()
    // Don't call setToken — this.token stays null

    const file = new File(['%PDF-test'], 'resume.pdf', { type: 'application/pdf' })
    await client.uploadResume(file)

    expect(fetchCalls.length).toBe(1)
    const headers = fetchCalls[0].headers as Record<string, string>
    expect(headers['Authorization']).toBe('Bearer ls-token-123')
  })

  it('retries on 401 after successful token refresh', async () => {
    localStorage.setItem('access_token', 'expired-token')
    localStorage.setItem('refresh_token', 'valid-refresh')

    let callCount = 0
    globalThis.fetch = vi.fn(async (url: string | URL | Request, _init?: RequestInit) => {
      callCount++
      const urlStr = typeof url === 'string' ? url : url.toString()

      if (urlStr.includes('/auth/refresh')) {
        return new Response(
          JSON.stringify({ access_token: 'new-access', refresh_token: 'new-refresh', token_type: 'bearer' }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        )
      }

      if (urlStr.includes('/resumes/upload')) {
        if (callCount === 1) {
          // First call: 401
          return new Response(JSON.stringify({ detail: 'Not authenticated' }), {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          })
        }
        // Retry: success
        return new Response(JSON.stringify({ id: 'r1', status: 'draft' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }

      return new Response('Not found', { status: 404 })
    }) as unknown as typeof fetch

    vi.resetModules()
    const { ApiClient } = await import('../services/api')
    const client = new ApiClient()

    const file = new File(['%PDF-test'], 'resume.pdf', { type: 'application/pdf' })
    const result = await client.uploadResume(file)

    expect(result).toEqual({ id: 'r1', status: 'draft' })
    // At least 3 calls: upload(401) + refresh + upload(200)
    expect(callCount).toBeGreaterThanOrEqual(3)
  })

  it('throws server error message instead of generic text', async () => {
    localStorage.setItem('access_token', 'valid-token')

    globalThis.fetch = vi.fn(async () => {
      return new Response(
        JSON.stringify({ message: 'Файл слишком большой (макс 10 МБ)' }),
        { status: 413, headers: { 'Content-Type': 'application/json' } },
      )
    }) as unknown as typeof fetch

    vi.resetModules()
    const { ApiClient } = await import('../services/api')
    const client = new ApiClient()

    const file = new File(['x'.repeat(100)], 'big.pdf', { type: 'application/pdf' })
    await expect(client.uploadResume(file)).rejects.toThrow('Файл слишком большой (макс 10 МБ)')
  })

  it('throws fallback message when server returns non-JSON error', async () => {
    localStorage.setItem('access_token', 'valid-token')

    globalThis.fetch = vi.fn(async () => {
      return new Response('Bad Gateway', {
        status: 502,
        statusText: 'Bad Gateway',
      })
    }) as unknown as typeof fetch

    vi.resetModules()
    const { ApiClient } = await import('../services/api')
    const client = new ApiClient()

    const file = new File(['%PDF-test'], 'resume.pdf', { type: 'application/pdf' })
    await expect(client.uploadResume(file)).rejects.toThrow()
  })

  it('does not set Content-Type header (FormData handles it)', async () => {
    localStorage.setItem('access_token', 'tok')

    const capturedHeaders: Record<string, string>[] = []
    globalThis.fetch = vi.fn(async (_url: string | URL | Request, init?: RequestInit) => {
      capturedHeaders.push(init?.headers as Record<string, string>)
      return new Response(JSON.stringify({ id: 'r1' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }) as unknown as typeof fetch

    vi.resetModules()
    const { ApiClient } = await import('../services/api')
    const client = new ApiClient()

    const file = new File(['%PDF-test'], 'resume.pdf', { type: 'application/pdf' })
    await client.uploadResume(file)

    expect(capturedHeaders[0]).not.toHaveProperty('Content-Type')
  })
})
