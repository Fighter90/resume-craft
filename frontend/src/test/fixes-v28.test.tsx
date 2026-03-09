/**
 * Tests for V28 fixes:
 * 1. KEY-CHECK-001: session.commit() before Celery delay (backend — verified via source tests)
 * 2. NAV-001: Plan upgrade Link uses normal React Router navigation (no preventDefault)
 * 3. isAuthError precision fix — no false positives on billing/timeout errors
 */
import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

/* eslint-disable @typescript-eslint/no-explicit-any */

// ─── Shared mocks ────────────────────────────────────────────

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

const mockUser = {
  id: 'u1',
  email: 'test@example.com',
  full_name: 'Тест Юзер',
  plan: 'free' as const,
  optimizations_used: 2,
  is_active: true,
  is_verified: true,
}

let currentMockUser: any = mockUser

vi.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    user: currentMockUser,
    token: 'test-token',
    isAuthenticated: true,
    loading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshUser: vi.fn().mockResolvedValue(undefined),
  }),
}))

vi.mock('../services/api', () => ({
  api: {
    getResumes: () => Promise.resolve([]),
    getRewriteHistory: () => Promise.resolve([]),
    getUserProfile: () => Promise.resolve(currentMockUser),
    updateAvatar: vi.fn(),
    deleteAvatar: vi.fn(),
    updateProfile: vi.fn(),
    deleteAIKey: vi.fn().mockResolvedValue({}),
    saveAIToggles: vi.fn().mockResolvedValue({}),
    saveSelectedModel: vi.fn().mockResolvedValue({}),
    getAIKeys: vi.fn().mockResolvedValue({ keys: [] }),
    getAIToggles: vi.fn().mockResolvedValue({ toggles: [] }),
    getSelectedModel: vi.fn().mockResolvedValue({ model: 'gigachat-pro', sub_model: null }),
    getSubModels: vi.fn().mockResolvedValue({ models: [] }),
    saveAIKey: vi.fn().mockResolvedValue({}),
  },
  ApiClient: vi.fn(),
}))

beforeEach(() => {
  currentMockUser = mockUser
  vi.clearAllMocks()
})

// ─── NAV-001 V28: Plan upgrade link — standard React Router Link ─────

describe('NAV-001 V28: Plan upgrade link uses standard Link navigation', () => {
  it('renders as <a> tag with correct href', async () => {
    const AppLayout = (await import('../components/layout/AppLayout')).default
    render(
      <MemoryRouter initialEntries={['/app/dashboard']}>
        <Routes>
          <Route path="/app" element={<AppLayout />}>
            <Route path="dashboard" element={<div>Dashboard</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )
    const link = screen.getByText(/Обновить до Pro/)
    expect(link.tagName).toBe('A')
    expect(link.getAttribute('href')).toBe('/app/settings/subscription')
  })

  it('does NOT use programmatic navigate on click', async () => {
    const AppLayout = (await import('../components/layout/AppLayout')).default
    render(
      <MemoryRouter initialEntries={['/app/dashboard']}>
        <Routes>
          <Route path="/app" element={<AppLayout />}>
            <Route path="dashboard" element={<div>Dashboard</div>} />
            <Route path="settings/subscription" element={<div>Subscription</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )
    const link = screen.getByText(/Обновить до Pro/)
    fireEvent.click(link)
    // V28: navigate should NOT be called with subscription path
    // (React Router Link handles navigation natively)
    expect(mockNavigate).not.toHaveBeenCalledWith('/app/settings/subscription')
  })

  it('is hidden for pro plan users', async () => {
    currentMockUser = { ...mockUser, plan: 'pro' }
    const AppLayout = (await import('../components/layout/AppLayout')).default
    render(
      <MemoryRouter initialEntries={['/app/dashboard']}>
        <Routes>
          <Route path="/app" element={<AppLayout />}>
            <Route path="dashboard" element={<div>Dashboard</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )
    expect(screen.queryByText(/Обновить до Pro/)).toBeNull()
  })

  it('is visible for standard plan users', async () => {
    currentMockUser = { ...mockUser, plan: 'standard' }
    const AppLayout = (await import('../components/layout/AppLayout')).default
    render(
      <MemoryRouter initialEntries={['/app/dashboard']}>
        <Routes>
          <Route path="/app" element={<AppLayout />}>
            <Route path="dashboard" element={<div>Dashboard</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )
    expect(screen.getByText(/Обновить до Pro/)).toBeTruthy()
  })
})

// ─── isAuthError precision: no false positives ───────────────

describe('isAuthError precision (V28)', () => {
  it('source does not match generic unavailable', async () => {
    // Read source to verify isAuthError is precise
    const fs = await import('fs')
    const src = fs.readFileSync('src/pages/wizard/ProcessingPage.tsx', 'utf-8')
    const fnStart = src.indexOf('function isAuthError')
    const fnEnd = src.indexOf('}', fnStart) + 1
    const fnBody = src.substring(fnStart, fnEnd)

    // Should NOT contain 'unavailable' as standalone check
    expect(fnBody).not.toContain("'unavailable'")
    expect(fnBody).not.toContain('"unavailable"')
  })

  it('source does not match generic auth', async () => {
    const fs = await import('fs')
    const src = fs.readFileSync('src/pages/wizard/ProcessingPage.tsx', 'utf-8')
    const fnStart = src.indexOf('function isAuthError')
    const fnEnd = src.indexOf('}', fnStart) + 1
    const fnBody = src.substring(fnStart, fnEnd)

    expect(fnBody).not.toContain("'auth'")
    expect(fnBody).not.toContain('"auth"')
  })

  it('source still catches api-ключ errors', async () => {
    const fs = await import('fs')
    const src = fs.readFileSync('src/pages/wizard/ProcessingPage.tsx', 'utf-8')
    const fnStart = src.indexOf('function isAuthError')
    const fnEnd = src.indexOf('}', fnStart) + 1
    const fnBody = src.substring(fnStart, fnEnd).toLowerCase()

    expect(fnBody).toContain('api-ключ')
    expect(fnBody).toContain('не настроен')
  })
})
