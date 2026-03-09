/**
 * Tests for V27 fixes:
 * 1. RESET-001: handleReset does NOT delete API keys — only resets toggles + model
 * 2. NAV-001: Plan upgrade link uses onClick with navigate() for bulletproof navigation
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

const mockDeleteAIKey = vi.fn().mockResolvedValue({})
const mockSaveAIToggles = vi.fn().mockResolvedValue({})
const mockSaveSelectedModel = vi.fn().mockResolvedValue({})
const mockGetAIKeys = vi.fn().mockResolvedValue({ keys: [] })
const mockGetAIToggles = vi.fn().mockResolvedValue({ toggles: [] })
const mockGetSelectedModel = vi.fn().mockResolvedValue({ provider: 'gigachat-pro', sub_model: null })
const mockGetSubModels = vi.fn().mockResolvedValue({ models: [] })

vi.mock('../services/api', () => ({
  api: {
    getResumes: () => Promise.resolve([]),
    getRewriteHistory: () => Promise.resolve([]),
    getUserProfile: () => Promise.resolve(currentMockUser),
    updateAvatar: vi.fn(),
    deleteAvatar: vi.fn(),
    updateProfile: vi.fn(),
    deleteAIKey: mockDeleteAIKey,
    saveAIToggles: mockSaveAIToggles,
    saveSelectedModel: mockSaveSelectedModel,
    getAIKeys: mockGetAIKeys,
    getAIToggles: mockGetAIToggles,
    getSelectedModel: mockGetSelectedModel,
    getSubModels: mockGetSubModels,
    saveAIKey: vi.fn().mockResolvedValue({}),
  },
  ApiClient: vi.fn(),
}))

beforeEach(() => {
  currentMockUser = mockUser
  vi.clearAllMocks()
})

// ─── NAV-001: Plan upgrade link with explicit navigate ───────

describe('NAV-001: Plan upgrade link navigation', () => {
  it('navigates via React Router Link on click (no preventDefault)', async () => {
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
    // V28: Link navigates natively via React Router (no programmatic navigate)
    expect(link.tagName).toBe('A')
    expect(link.getAttribute('href')).toBe('/app/settings/subscription')
    // Click should NOT call programmatic navigate — navigation happens via Link
    fireEvent.click(link)
    expect(mockNavigate).not.toHaveBeenCalledWith('/app/settings/subscription')
  })

  it('renders as <a> tag with correct href for accessibility', async () => {
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

  it('does not render for pro users', async () => {
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
})

// ─── RESET-001: handleReset never calls deleteAIKey ──────────

describe('RESET-001: Reset preserves API keys', () => {
  it('clicking reset does not call deleteAIKey', async () => {
    const SettingsAiPage = (await import('../pages/settings/SettingsAiPage')).default
    render(
      <MemoryRouter>
        <SettingsAiPage />
      </MemoryRouter>,
    )

    // Wait for initial load
    await vi.waitFor(() => {
      expect(screen.getByText(/Сбросить/)).toBeTruthy()
    })

    const resetBtn = screen.getByText(/Сбросить/)
    fireEvent.click(resetBtn)

    // Give async handler time to execute
    await vi.waitFor(() => {
      expect(mockDeleteAIKey).not.toHaveBeenCalled()
    })
  })

  it('clicking reset saves default toggles to server', async () => {
    const SettingsAiPage = (await import('../pages/settings/SettingsAiPage')).default
    render(
      <MemoryRouter>
        <SettingsAiPage />
      </MemoryRouter>,
    )

    await vi.waitFor(() => {
      expect(screen.getByText(/Сбросить/)).toBeTruthy()
    })

    const resetBtn = screen.getByText(/Сбросить/)
    fireEvent.click(resetBtn)

    await vi.waitFor(() => {
      expect(mockSaveAIToggles).toHaveBeenCalled()
    })
  })

  it('clicking reset saves default model to server', async () => {
    const SettingsAiPage = (await import('../pages/settings/SettingsAiPage')).default
    render(
      <MemoryRouter>
        <SettingsAiPage />
      </MemoryRouter>,
    )

    await vi.waitFor(() => {
      expect(screen.getByText(/Сбросить/)).toBeTruthy()
    })

    const resetBtn = screen.getByText(/Сбросить/)
    fireEvent.click(resetBtn)

    await vi.waitFor(() => {
      expect(mockSaveSelectedModel).toHaveBeenCalled()
    })
  })
})
