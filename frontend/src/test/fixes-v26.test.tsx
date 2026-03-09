/**
 * Tests for V26 fixes:
 * 1. NAV-001: AppLayout — plan-upgrade uses Link (not NavLink), clickable
 * 2. EMAIL-VERIFY-001: SettingsProfilePage — email verification status dynamic
 * 3. EMAIL-VERIFY-001: DashboardPage — banner consistency with is_verified
 */
import React from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

/* eslint-disable @typescript-eslint/no-explicit-any */

// ─── Mock Auth Context ───────────────────────────────────────

const mockUser = {
  id: 'u1',
  email: 'test@example.com',
  full_name: 'Тест Юзер',
  plan: 'free' as const,
  optimizations_used: 2,
  is_active: true,
  is_verified: true,
}

const mockUserUnverified = {
  ...mockUser,
  is_verified: false,
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
  },
  ApiClient: vi.fn(),
}))

beforeEach(() => {
  currentMockUser = mockUser
})

// ─── NAV-001: Plan upgrade link uses Link ────────────────────

describe('NAV-001: Plan upgrade link', () => {
  it('renders as regular Link with correct href', async () => {
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
    expect(link.className).toContain('plan-upgrade')
  })

  it('is hidden for pro users', async () => {
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

// ─── EMAIL-VERIFY-001: Profile page email verification ───────

describe('EMAIL-VERIFY-001: Profile email verification', () => {
  it('shows "Подтверждён" when is_verified is true', async () => {
    currentMockUser = { ...mockUser, is_verified: true }
    const SettingsProfilePage = (await import('../pages/settings/SettingsProfilePage')).default
    render(
      <MemoryRouter>
        <SettingsProfilePage />
      </MemoryRouter>,
    )
    expect(screen.getByText('Подтверждён')).toBeTruthy()
    expect(screen.queryByText(/Не подтверждён/)).toBeNull()
  })

  it('shows "Не подтверждён" when is_verified is false', async () => {
    currentMockUser = { ...mockUser, is_verified: false }
    const SettingsProfilePage = (await import('../pages/settings/SettingsProfilePage')).default
    render(
      <MemoryRouter>
        <SettingsProfilePage />
      </MemoryRouter>,
    )
    expect(screen.getByText(/Не подтверждён/)).toBeTruthy()
    expect(screen.queryByText('Подтверждён')).toBeNull()
  })
})

// ─── EMAIL-VERIFY-001: Dashboard banner consistency ──────────

describe('EMAIL-VERIFY-001: Dashboard banner', () => {
  it('shows verification banner when is_verified is false', async () => {
    currentMockUser = { ...mockUserUnverified }
    const DashboardPage = (await import('../pages/dashboard/DashboardPage')).default
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )
    expect(screen.getByText(/Подтвердите email/)).toBeTruthy()
  })

  it('hides verification banner when is_verified is true', async () => {
    currentMockUser = { ...mockUser, is_verified: true }
    const DashboardPage = (await import('../pages/dashboard/DashboardPage')).default
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )
    expect(screen.queryByText(/Подтвердите email/)).toBeNull()
  })
})
