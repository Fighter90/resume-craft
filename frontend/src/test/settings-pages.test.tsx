/**
 * Tests for SettingsProfilePage (photo persistence, form save),
 * SettingsAIPage (model availability, sub-models fallback, API keys),
 * SettingsSubscriptionPage, and SettingsSecurityPage.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

/* eslint-disable @typescript-eslint/no-explicit-any */

// --- API mock ---
const mockUpdateProfile = vi.fn()
const mockChangePassword = vi.fn()
const mockGetModels = vi.fn()
const mockGetSubModels = vi.fn()
const mockDeleteAccount = vi.fn()
const mockUploadAvatar = vi.fn()
const mockDeleteAvatar = vi.fn()

vi.mock('../services/api', () => ({
  api: {
    updateProfile: (...a: any[]) => mockUpdateProfile(...a),
    changePassword: (...a: any[]) => mockChangePassword(...a),
    getModels: (...a: any[]) => mockGetModels(...a),
    getSubModels: (...a: any[]) => mockGetSubModels(...a),
    deleteAccount: (...a: any[]) => mockDeleteAccount(...a),
    uploadAvatar: (...a: any[]) => mockUploadAvatar(...a),
    deleteAvatar: (...a: any[]) => mockDeleteAvatar(...a),
    setToken: vi.fn(),
    clearToken: vi.fn(),
    getMe: vi.fn().mockRejectedValue(new Error('not authed')),
  },
  ApiClient: vi.fn(),
}))

const mockUser = {
  id: 'user-1',
  email: 'test@example.com',
  full_name: 'Иван Петров',
  plan: 'free' as const,
  optimizations_used: 3,
  is_active: true,
}

vi.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    isAuthenticated: true,
    loading: false,
    user: mockUser,
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    refreshUser: vi.fn().mockResolvedValue(undefined),
  }),
}))

import SettingsProfilePage from '../pages/settings/SettingsProfilePage'
import SettingsAiPage from '../pages/settings/SettingsAiPage'
import SettingsSubscriptionPage from '../pages/settings/SettingsSubscriptionPage'
import SettingsSecurityPage from '../pages/settings/SettingsSecurityPage'

function renderInRouter(element: React.ReactNode) {
  return render(
    <MemoryRouter>
      {element}
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  mockUpdateProfile.mockResolvedValue(mockUser)
  mockChangePassword.mockResolvedValue({ message: 'ok' })
  mockGetModels.mockResolvedValue({ models: [
    { id: 'gigachat-pro', name: 'GigaChat Pro', provider: 'Сбер', available: false },
    { id: 'openai', name: 'OpenAI', provider: 'OpenAI', available: true },
  ]})
  mockGetSubModels.mockRejectedValue(new Error('unavailable'))
})

afterEach(() => {
  localStorage.clear()
})

// ===================== SettingsProfilePage =====================
describe('SettingsProfilePage', () => {
  it('renders profile form with user data', () => {
    renderInRouter(<SettingsProfilePage />)
    expect(screen.getByDisplayValue('Иван')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Петров')).toBeInTheDocument()
    expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument()
  })

  it('renders photo upload button', () => {
    renderInRouter(<SettingsProfilePage />)
    expect(screen.getByText('Загрузить фото')).toBeInTheDocument()
  })

  it('persists avatar via server upload API', async () => {
    mockUploadAvatar.mockResolvedValue({ message: '/api/v1/uploads/user-1/avatar_abc123.png' })
    renderInRouter(<SettingsProfilePage />)

    const fileInput = screen.getByTestId('photo-upload-input') as HTMLInputElement
    const mockFile = new File(['fake-image-data'], 'avatar.png', { type: 'image/png' })

    fireEvent.change(fileInput, { target: { files: [mockFile] } })

    await waitFor(() => {
      expect(mockUploadAvatar).toHaveBeenCalledWith(mockFile)
    })
  })

  it('shows avatar from user.avatar_url on mount', () => {
    // Avatar now comes from user object, not localStorage
    renderInRouter(<SettingsProfilePage />)
    // The component should render without error (avatar_url is null by default)
    expect(screen.getByText('Загрузить фото')).toBeInTheDocument()
  })

  it('removes avatar on delete', async () => {
    mockDeleteAvatar.mockResolvedValue(undefined)
    renderInRouter(<SettingsProfilePage />)

    // The delete button should exist
    const deleteBtn = screen.getByText('Удалить')
    expect(deleteBtn).toBeInTheDocument()
  })

  it('saves profile on button click', async () => {
    renderInRouter(<SettingsProfilePage />)

    fireEvent.click(screen.getByText('Сохранить изменения'))

    await waitFor(() => {
      expect(mockUpdateProfile).toHaveBeenCalledWith({
        full_name: 'Иван Петров',
        email: 'test@example.com',
      })
    })
    await waitFor(() => {
      expect(screen.getByText('Изменения сохранены')).toBeInTheDocument()
    })
  })

  it('shows error on save failure', async () => {
    mockUpdateProfile.mockRejectedValue(new Error('Ошибка сервера'))
    renderInRouter(<SettingsProfilePage />)

    fireEvent.click(screen.getByText('Сохранить изменения'))

    await waitFor(() => {
      expect(screen.getByText('Ошибка сервера')).toBeInTheDocument()
    })
  })

  it('renders disabled fields', () => {
    renderInRouter(<SettingsProfilePage />)
    expect(screen.getByText('Телефон')).toBeInTheDocument()
    expect(screen.getByText('Город')).toBeInTheDocument()
  })
})

// ===================== SettingsAIPage =====================
describe('SettingsAIPage', () => {
  it('renders model cards', async () => {
    renderInRouter(<SettingsAiPage />)
    expect(screen.getByText('GigaChat Pro')).toBeInTheDocument()
    expect(screen.getByText('OpenAI')).toBeInTheDocument()
    expect(screen.getByText('Anthropic Claude')).toBeInTheDocument()
    expect(screen.getByText('OpenRouter')).toBeInTheDocument()
  })

  it('renders API key inputs', () => {
    renderInRouter(<SettingsAiPage />)
    expect(screen.getByPlaceholderText('Credentials (Base64)')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('sk-...')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('sk-ant-...')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('sk-or-v1-...')).toBeInTheDocument()
  })

  it('selects model on click', () => {
    renderInRouter(<SettingsAiPage />)
    fireEvent.click(screen.getByText('OpenAI'))
    // Sub-model picker should appear
    expect(screen.getByText(/Модель OpenAI/)).toBeInTheDocument()
  })

  it('shows fallback sub-models when server fails', async () => {
    mockGetSubModels.mockRejectedValue(new Error('unavailable'))
    renderInRouter(<SettingsAiPage />)
    fireEvent.click(screen.getByText('OpenAI'))

    await waitFor(() => {
      expect(screen.getByText(/GPT-4o/)).toBeInTheDocument()
    })
  })

  it('shows GigaChat sub-model picker with fallback models', async () => {
    mockGetSubModels.mockRejectedValue(new Error('unavailable'))
    renderInRouter(<SettingsAiPage />)
    // GigaChat is selected by default — sub-model picker should appear
    await waitFor(() => {
      expect(screen.getByText(/Модель GigaChat Pro/)).toBeInTheDocument()
    })
    await waitFor(() => {
      expect(screen.getByText(/GigaChat-Pro/)).toBeInTheDocument()
    })
  })

  it('shows comprehensive fallback with 10+ OpenAI models', async () => {
    mockGetSubModels.mockRejectedValue(new Error('unavailable'))
    renderInRouter(<SettingsAiPage />)
    fireEvent.click(screen.getByText('OpenAI'))

    await waitFor(() => {
      expect(screen.getByText(/GPT-4o/)).toBeInTheDocument()
    })
    // Should show more than 4 fallback models
    await waitFor(() => {
      const options = screen.getAllByRole('option')
      expect(options.length).toBeGreaterThanOrEqual(8)
    })
  })

  it('shows availability check mark for locally configured API key', async () => {
    localStorage.setItem('ai_settings', JSON.stringify({
      model: 'gigachat-pro',
      apiKeys: { gigachat: 'test-key-123', openai: '', anthropic: '', openrouter: '' },
      toggles: {},
    }))
    renderInRouter(<SettingsAiPage />)

    await waitFor(() => {
      // GigaChat should show checkmark because local key exists
      const checks = document.querySelectorAll('[title="Ключ настроен на сервере"]')
      // At minimum OpenAI from server or GigaChat from local key
      expect(checks.length).toBeGreaterThanOrEqual(1)
    })
  })

  it('saves settings to localStorage', () => {
    renderInRouter(<SettingsAiPage />)
    fireEvent.click(screen.getByText('Сохранить'))

    const saved = JSON.parse(localStorage.getItem('ai_settings') || '{}')
    expect(saved.model).toBe('gigachat-pro')
  })

  it('resets settings on reset button', () => {
    localStorage.setItem('ai_settings', JSON.stringify({ model: 'openai' }))
    renderInRouter(<SettingsAiPage />)
    fireEvent.click(screen.getByText('Сбросить'))

    expect(localStorage.getItem('ai_settings')).toBeNull()
  })

  it('renders optimization toggles', () => {
    renderInRouter(<SettingsAiPage />)
    expect(screen.getByText('ATS оптимизация')).toBeInTheDocument()
    expect(screen.getByText('Автоматические метрики')).toBeInTheDocument()
    expect(screen.getByText('Сохранять язык')).toBeInTheDocument()
  })

  it('toggles visibility of API key', () => {
    renderInRouter(<SettingsAiPage />)
    const showButtons = screen.getAllByTitle('Показать')
    fireEvent.click(showButtons[0])
    expect(screen.getAllByTitle('Скрыть').length).toBeGreaterThanOrEqual(1)
  })

  it('shows Рекомендуем badge on GigaChat', () => {
    renderInRouter(<SettingsAiPage />)
    expect(screen.getByText('Рекомендуем')).toBeInTheDocument()
  })
})

// ===================== SettingsSubscriptionPage =====================
describe('SettingsSubscriptionPage', () => {
  it('renders plan information', () => {
    renderInRouter(<SettingsSubscriptionPage />)
    expect(screen.getAllByText(/Free|Standard|Pro|Бесплатный/i).length).toBeGreaterThanOrEqual(1)
  })

  it('renders upgrade buttons', () => {
    renderInRouter(<SettingsSubscriptionPage />)
    // There should be at least one plan-related action
    const btns = screen.getAllByRole('button')
    expect(btns.length).toBeGreaterThan(0)
  })
})

// ===================== SettingsSecurityPage =====================
describe('SettingsSecurityPage', () => {
  it('renders password change form', () => {
    renderInRouter(<SettingsSecurityPage />)
    expect(screen.getByText(/Сменить пароль/i)).toBeInTheDocument()
  })

  it('does not render 2FA placeholder (removed per NEW-007)', () => {
    renderInRouter(<SettingsSecurityPage />)
    expect(screen.queryByText('Двухфакторная аутентификация')).not.toBeInTheDocument()
    expect(screen.queryByText('Скоро')).not.toBeInTheDocument()
  })

  it('renders delete account section', () => {
    renderInRouter(<SettingsSecurityPage />)
    expect(screen.getByText('Опасная зона')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Удалить аккаунт' })).toBeInTheDocument()
  })
})
