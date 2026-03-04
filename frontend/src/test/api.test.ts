import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ApiClient } from '../services/api'

describe('ApiClient', () => {
  let client: ApiClient

  beforeEach(() => {
    client = new ApiClient()
    localStorage.clear()
  })

  it('creates instance with default base URL', () => {
    expect(client).toBeDefined()
  })

  it('sets token in localStorage on setToken', () => {
    client.setToken('test-token-123')
    expect(localStorage.getItem('token')).toBe('test-token-123')
  })

  it('clears token on clearToken', () => {
    localStorage.setItem('token', 'some-token')
    client.clearToken()
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('sends authorization header when token is set', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: 'ok' }),
    })
    vi.stubGlobal('fetch', mockFetch)

    localStorage.setItem('token', 'bearer-test')
    await client.healthCheck()

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/health'),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer bearer-test',
        }),
      })
    )

    vi.unstubAllGlobals()
  })

  it('login calls POST /auth/login', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ access_token: 'tok', token_type: 'bearer' }),
    })
    vi.stubGlobal('fetch', mockFetch)

    const result = await client.login('user@test.com', 'pass123')
    expect(result.access_token).toBe('tok')

    const [url, opts] = mockFetch.mock.calls[0]
    expect(url).toContain('/auth/login')
    expect(opts.method).toBe('POST')

    vi.unstubAllGlobals()
  })

  it('register calls POST /auth/register', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: '1', email: 'new@test.com' }),
    })
    vi.stubGlobal('fetch', mockFetch)

    await client.register('new@test.com', 'Password1', 'Test User')

    const [url, opts] = mockFetch.mock.calls[0]
    expect(url).toContain('/auth/register')
    expect(opts.method).toBe('POST')

    vi.unstubAllGlobals()
  })

  it('throws on non-ok response', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: 'Unauthorized' }),
    })
    vi.stubGlobal('fetch', mockFetch)

    await expect(client.login('bad@test.com', 'wrong')).rejects.toThrow()

    vi.unstubAllGlobals()
  })
})
