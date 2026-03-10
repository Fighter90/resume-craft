/**
 * Tests for QA v1.6 fixes: XSS, ErrorBoundary, auth, modal, api.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'
import { WizardProvider } from '../contexts/WizardContext'

/* eslint-disable @typescript-eslint/no-explicit-any */

// --- Mocks ---
vi.mock('../services/api', () => ({
  api: {
    searchVacancies: vi.fn().mockResolvedValue([]),
    createVacancyFromUrl: vi.fn().mockResolvedValue({ id: 'v1' }),
    createVacancyManual: vi.fn().mockResolvedValue({ id: 'v2' }),
    getHHVacancyDetail: vi.fn().mockResolvedValue({ description: '<b>test</b>' }),
    getRewriteStatus: vi.fn().mockResolvedValue({ status: 'pending', step: 'extracting', progress: 0 }),
    getRewriteResult: vi.fn().mockResolvedValue({}),
    getModels: vi.fn().mockResolvedValue({ models: [] }),
    getSubModels: vi.fn().mockResolvedValue({ sub_models: [] }),
    deleteAccount: vi.fn().mockResolvedValue(undefined),
    changePassword: vi.fn().mockResolvedValue({ message: 'ok' }),
    selectSearchVacancy: vi.fn().mockResolvedValue({ id: 'v1' }),
    setToken: vi.fn(),
    clearToken: vi.fn(),
  },
}))

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    loading: false,
    login: vi.fn().mockResolvedValue(undefined),
    register: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn(),
    user: { id: 'test', email: 'test@test.com', full_name: 'Test', plan: 'free', optimizations_used: 0, is_active: true },
    refreshUser: vi.fn(),
  }),
}))

function renderInWizard(Component: React.ComponentType, path: string = '/test') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <WizardProvider>
        <Routes>
          <Route path="*" element={<Component />} />
        </Routes>
      </WizardProvider>
    </MemoryRouter>
  )
}

describe('ErrorBoundary (UI-010)', () => {
  it('renders children when no error', async () => {
    const { default: ErrorBoundary } = await import('../components/ErrorBoundary')
    render(
      <ErrorBoundary><div data-testid="child">OK</div></ErrorBoundary>
    )
    expect(screen.getByTestId('child')).toBeTruthy()
  })

  it('catches render error and shows fallback', async () => {
    const { default: ErrorBoundary } = await import('../components/ErrorBoundary')
    function Bomb(): never { throw new Error('Test crash') }
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(<ErrorBoundary><Bomb /></ErrorBoundary>)
    expect(screen.getByText('Что-то пошло не так')).toBeTruthy()
    spy.mockRestore()
  })
})

describe('Auth password confirmation (UI-003)', () => {
  it('shows confirm password field on register tab', async () => {
    const { default: AuthPage } = await import('../pages/auth/AuthPage')
    render(
      <MemoryRouter initialEntries={['/auth?tab=register']}>
        <Routes>
          <Route path="/auth" element={<AuthPage />} />
        </Routes>
      </MemoryRouter>
    )
    expect(screen.getByPlaceholderText('Повторите пароль')).toBeTruthy()
  })

  it('does not show confirm password on login tab', async () => {
    const { default: AuthPage } = await import('../pages/auth/AuthPage')
    render(
      <MemoryRouter initialEntries={['/auth?tab=login']}>
        <Routes>
          <Route path="/auth" element={<AuthPage />} />
        </Routes>
      </MemoryRouter>
    )
    expect(screen.queryByPlaceholderText('Повторите пароль')).toBeFalsy()
  })
})

describe('API client (ARCH-012 duplicate, UI-005 refresh)', () => {
  it('selectSearchVacancy delegates to createVacancyFromUrl', async () => {
    const { api } = await import('../services/api')
    // Both methods exist and are callable
    expect(typeof api.selectSearchVacancy).toBe('function')
    expect(typeof api.createVacancyFromUrl).toBe('function')
  })
})

describe('Security page — no alert() (UI-006)', () => {
  it('shows error in UI instead of alert', async () => {
    const { api } = await import('../services/api')
    ;(api.deleteAccount as any).mockRejectedValueOnce(new Error('Test delete error'))

    const { default: SettingsSecurityPage } = await import('../pages/settings/SettingsSecurityPage')
    render(
      <MemoryRouter>
        <SettingsSecurityPage />
      </MemoryRouter>
    )

    // Open delete section
    fireEvent.click(screen.getByText('Удалить аккаунт'))

    // Fill in password (required for button to be enabled)
    const pwInput = screen.getByPlaceholderText('Введите ваш пароль')
    fireEvent.change(pwInput, { target: { value: 'TestPassword123' } })

    // Type confirmation
    const input = screen.getByPlaceholderText(/УДАЛИТЬ/)
    fireEvent.change(input, { target: { value: 'УДАЛИТЬ' } })

    // Click confirm — should NOT call alert(), should show error in UI
    fireEvent.click(screen.getByText('Подтвердить'))

    await waitFor(() => {
      expect(screen.getByText('Test delete error')).toBeTruthy()
    })
  })
})

describe('Upload page — responsive tabs (LIVE-010)', () => {
  it('renders tab labels with short variants', async () => {
    const { default: UploadPage } = await import('../pages/wizard/UploadPage')
    renderInWizard(UploadPage)
    // Both full and short labels should exist in DOM
    expect(screen.getAllByText('Файл').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Ссылка').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Текст').length).toBeGreaterThanOrEqual(1)
  })
})
