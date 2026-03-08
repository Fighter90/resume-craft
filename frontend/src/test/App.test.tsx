import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'
import App from '../App'

 

// Mock AuthContext so ProtectedRoute sees isAuthenticated = true
vi.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    isAuthenticated: true,
    loading: false,
    user: { id: 'u1', email: 'test@test.com', full_name: 'Test User', plan: 'free', optimizations_used: 0, is_active: true },
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    refreshUser: vi.fn(),
  }),
}))

// Mock API to prevent real network calls
vi.mock('../services/api', () => ({
  api: {
    setToken: vi.fn(),
    clearToken: vi.fn(),
    getMe: vi.fn().mockRejectedValue(new Error('mocked')),
    getResumes: vi.fn().mockResolvedValue([]),
    getRewriteHistory: vi.fn().mockResolvedValue([]),
    searchVacancies: vi.fn().mockResolvedValue({ items: [] }),
  },
  ApiClient: vi.fn(),
}))

function renderApp(route = '/') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <App />
    </MemoryRouter>
  )
}

describe('App Router', () => {
  it('renders landing page at /', () => {
    renderApp('/')
    expect(screen.getByText(/Загрузите резюме, выберите вакансию/i)).toBeInTheDocument()
  })

  it('renders auth page at /auth', () => {
    renderApp('/auth')
    expect(screen.getByRole('heading', { name: /войти/i })).toBeInTheDocument()
  })

  it('renders pricing page at /pricing', () => {
    renderApp('/pricing')
    expect(screen.getByRole('heading', { name: /подходящий план/i })).toBeInTheDocument()
  })

  it('renders password recovery at /password-recovery', () => {
    renderApp('/password-recovery')
    expect(screen.getByText('Восстановление пароля')).toBeInTheDocument()
  })

  it('renders email verify at /email-verify', () => {
    renderApp('/email-verify')
    expect(screen.getByRole('heading', { name: /аккаунт создан/i })).toBeInTheDocument()
  })

  it('renders 404 for unknown routes', () => {
    renderApp('/some-unknown-route')
    expect(screen.getByText('404')).toBeInTheDocument()
    expect(screen.getByText('Страница не найдена')).toBeInTheDocument()
  })

  it('renders privacy page at /privacy', () => {
    renderApp('/privacy')
    expect(screen.getByText('Политика конфиденциальности')).toBeInTheDocument()
  })

  it('renders terms page at /terms', () => {
    renderApp('/terms')
    expect(screen.getByText('Правила сервиса')).toBeInTheDocument()
  })

  it('renders about page at /about', () => {
    renderApp('/about')
    expect(screen.getByText('О сервисе ResumeCraft')).toBeInTheDocument()
  })

  it('renders dashboard at /app/dashboard', () => {
    renderApp('/app/dashboard')
    expect(screen.getByRole('heading', { name: /добрый день/i })).toBeInTheDocument()
  })

  it('renders resumes at /app/resumes', () => {
    renderApp('/app/resumes')
    expect(screen.getByRole('heading', { name: /мои резюме/i })).toBeInTheDocument()
  })

  it('renders upload wizard at /app/upload', () => {
    renderApp('/app/upload')
    expect(screen.getByRole('heading', { name: /загрузите ваше резюме/i })).toBeInTheDocument()
  })

  it('renders vacancy wizard at /app/vacancy', () => {
    renderApp('/app/vacancy')
    expect(screen.getByText('Выберите целевую вакансию')).toBeInTheDocument()
  })

  it('renders models wizard at /app/models', () => {
    renderApp('/app/models')
    expect(screen.getByText('Выберите AI-модель')).toBeInTheDocument()
  })

  it('renders results at /app/results', () => {
    renderApp('/app/results')
    // Without a task_id, ResultsPage shows "Нет данных"
    expect(screen.getByText(/нет данных/i)).toBeInTheDocument()
  })

  it('renders editor at /app/editor — redirects to upload without data (UI-012)', async () => {
    renderApp('/app/editor')
    // EditorPage guard redirects to /app/upload when no result/resumeId
    await waitFor(() => {
      expect(screen.getByText(/загрузите ваше резюме/i)).toBeInTheDocument()
    })
  })

  it('renders export at /app/export', () => {
    renderApp('/app/export')
    expect(screen.getByRole('heading', { name: /экспорт резюме/i })).toBeInTheDocument()
  })

  it('renders history at /app/history', () => {
    renderApp('/app/history')
    expect(screen.getByRole('heading', { name: /история/i })).toBeInTheDocument()
  })

  it('renders settings at /app/settings/profile', () => {
    renderApp('/app/settings/profile')
    expect(screen.getByRole('heading', { name: /настройки/i })).toBeInTheDocument()
  })

  it('renders settings AI at /app/settings/ai', () => {
    renderApp('/app/settings/ai')
    expect(screen.getByText('AI-модель по умолчанию')).toBeInTheDocument()
  })

  it('renders settings subscription at /app/settings/subscription', () => {
    renderApp('/app/settings/subscription')
    expect(screen.getByRole('heading', { name: /текущий план/i })).toBeInTheDocument()
  })

  it('renders settings security at /app/settings/security', () => {
    renderApp('/app/settings/security')
    expect(screen.getByRole('heading', { name: /сменить пароль/i })).toBeInTheDocument()
  })
})
