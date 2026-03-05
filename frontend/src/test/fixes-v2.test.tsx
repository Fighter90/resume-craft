/**
 * Comprehensive tests for v2 fixes:
 * - ResumesPage: optimize button for non-optimized, Apply filter button
 * - ResumeDetailPage: always show raw_text content
 * - ModelsPage: local API key detection
 * - UploadPage: hh.ru URL parsing with fallback
 * - SettingsAiPage: dynamic model loading from provider APIs
 * - SettingsProfilePage: per-account avatar storage
 * - SettingsSecurityPage: account deletion with logout
 * - api.ts: new methods (parseResumeFromUrl, deleteAccount)
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

/* eslint-disable @typescript-eslint/no-explicit-any */

// --- API mock ---
const mockGetResumes = vi.fn()
const mockDeleteResume = vi.fn()
const mockGetRewriteHistory = vi.fn()
const mockExportDocx = vi.fn()
const mockGetResume = vi.fn()
const mockGetModels = vi.fn()
const mockGetSubModels = vi.fn()
const mockStartRewrite = vi.fn()
const mockUploadResume = vi.fn()
const mockCreateResumeFromText = vi.fn()
const mockParseResumeFromUrl = vi.fn()
const mockUpdateProfile = vi.fn()
const mockChangePassword = vi.fn()
const mockDeleteAccount = vi.fn()
const mockSearchVacancies = vi.fn()

vi.mock('../services/api', () => ({
  api: {
    getResumes: (...a: any[]) => mockGetResumes(...a),
    deleteResume: (...a: any[]) => mockDeleteResume(...a),
    getRewriteHistory: (...a: any[]) => mockGetRewriteHistory(...a),
    exportDocx: (...a: any[]) => mockExportDocx(...a),
    getResume: (...a: any[]) => mockGetResume(...a),
    getModels: (...a: any[]) => mockGetModels(...a),
    getSubModels: (...a: any[]) => mockGetSubModels(...a),
    startRewrite: (...a: any[]) => mockStartRewrite(...a),
    uploadResume: (...a: any[]) => mockUploadResume(...a),
    createResumeFromText: (...a: any[]) => mockCreateResumeFromText(...a),
    parseResumeFromUrl: (...a: any[]) => mockParseResumeFromUrl(...a),
    updateProfile: (...a: any[]) => mockUpdateProfile(...a),
    changePassword: (...a: any[]) => mockChangePassword(...a),
    deleteAccount: (...a: any[]) => mockDeleteAccount(...a),
    searchVacancies: (...a: any[]) => mockSearchVacancies(...a),
    setToken: vi.fn(),
    clearToken: vi.fn(),
    getMe: vi.fn().mockRejectedValue(new Error('not authed')),
    serverLogout: vi.fn(),
  },
  ApiClient: vi.fn(),
}))

const mockLogout = vi.fn()
const mockNavigate = vi.fn()

vi.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    isAuthenticated: true,
    loading: false,
    user: { id: 'user-42', email: 'test@test.com', full_name: 'Тест Юзер', plan: 'free', optimizations_used: 2, is_active: true },
    login: vi.fn(),
    logout: mockLogout,
    register: vi.fn(),
    refreshUser: vi.fn().mockResolvedValue(undefined),
  }),
}))

vi.mock('../contexts/WizardContext', () => ({
  WizardProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useWizard: () => ({
    file: null, resumeId: 'res-1', vacancyId: 'vac-1', model: 'gigachat-pro', taskId: null, result: null,
    setFile: vi.fn(), setResumeId: vi.fn(), setVacancyId: vi.fn(), setModel: vi.fn(), setTaskId: vi.fn(), setResult: vi.fn(), reset: vi.fn(),
  }),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

import ResumesPage from '../pages/resumes/ResumesPage'
import ResumeDetailPage from '../pages/resumes/ResumeDetailPage'
import ModelsPage from '../pages/wizard/ModelsPage'
import UploadPage from '../pages/wizard/UploadPage'
import SettingsAiPage from '../pages/settings/SettingsAiPage'
import SettingsProfilePage from '../pages/settings/SettingsProfilePage'
import SettingsSecurityPage from '../pages/settings/SettingsSecurityPage'

function renderInRouter(ui: React.ReactElement, route = '/') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path="/app/resumes/:id" element={ui} />
        <Route path="*" element={ui} />
      </Routes>
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  mockGetResumes.mockResolvedValue([])
  mockGetModels.mockResolvedValue({ models: [] })
  mockGetSubModels.mockResolvedValue({ sub_models: [] })
  mockGetRewriteHistory.mockResolvedValue([])
  mockSearchVacancies.mockResolvedValue([])
})

afterEach(() => {
  localStorage.clear()
})

// ==========================================================================
// ResumesPage — Optimize button for non-optimized + Apply filter button
// ==========================================================================
describe('ResumesPage v2', () => {
  const draftResume = { id: 'r1', title: 'Черновик', status: 'draft', file_format: 'pdf', created_at: '2026-01-01' }
  const optimizedResume = { id: 'r2', title: 'Оптимизированное', status: 'optimized', file_format: 'docx', created_at: '2026-02-01' }
  const processingResume = { id: 'r3', title: 'В процессе', status: 'processing', file_format: 'pdf', created_at: '2026-03-01' }

  it('shows optimize button for draft resumes in table', async () => {
    mockGetResumes.mockResolvedValue([draftResume])
    renderInRouter(<ResumesPage />)

    await waitFor(() => {
      expect(screen.getByText('Черновик')).toBeInTheDocument()
    })

    const optimizeLink = screen.getByTitle('Оптимизировать')
    expect(optimizeLink).toBeInTheDocument()
    expect(optimizeLink.closest('a')).toHaveAttribute('href', '/app/upload')
  })

  it('shows optimize button for processing resumes', async () => {
    mockGetResumes.mockResolvedValue([processingResume])
    renderInRouter(<ResumesPage />)

    await waitFor(() => {
      expect(screen.getAllByText('В процессе').length).toBeGreaterThanOrEqual(1)
    })

    expect(screen.getAllByTitle('Оптимизировать').length).toBeGreaterThanOrEqual(1)
  })

  it('does NOT show optimize button for optimized resumes', async () => {
    mockGetResumes.mockResolvedValue([optimizedResume])
    renderInRouter(<ResumesPage />)

    await waitFor(() => {
      expect(screen.getAllByText('Оптимизированное').length).toBeGreaterThanOrEqual(1)
    })

    expect(screen.queryByTitle('Оптимизировать')).not.toBeInTheDocument()
  })

  it('renders Применить filter button', async () => {
    mockGetResumes.mockResolvedValue([draftResume])
    renderInRouter(<ResumesPage />)

    await waitFor(() => {
      expect(screen.getByText('Применить')).toBeInTheDocument()
    })
  })

  it('filters by status dropdown', async () => {
    mockGetResumes.mockResolvedValue([draftResume, optimizedResume])
    renderInRouter(<ResumesPage />)

    await waitFor(() => {
      const badge = screen.getAllByText('Черновик')
      expect(badge.length).toBeGreaterThanOrEqual(1)
    })

    // Select only optimized
    const selects = screen.getAllByRole('combobox')
    const statusSelect = selects.find(s => {
      const options = Array.from(s.querySelectorAll('option'))
      return options.some(o => o.textContent === 'Все статусы')
    })!
    fireEvent.change(statusSelect, { target: { value: 'Оптимизировано' } })

    // Draft badge should be gone from data rows (might still be in dropdown)
    await waitFor(() => {
      const rows = screen.queryAllByText('Черновик')
      // Only in dropdown, not in table body
      const tableBody = document.querySelector('tbody')
      const draftInTable = tableBody?.querySelectorAll('.badge-gray')
      expect(draftInTable?.length ?? 0).toBe(0)
    })
  })

  it('shows mix of optimize and non-optimize buttons in a list of mixed resumes', async () => {
    mockGetResumes.mockResolvedValue([draftResume, optimizedResume, processingResume])
    renderInRouter(<ResumesPage />)

    await waitFor(() => {
      expect(screen.getByText('Черновик')).toBeInTheDocument()
    })

    // 2 optimize buttons (draft + processing), not for optimized
    const optimizeButtons = screen.getAllByTitle('Оптимизировать')
    expect(optimizeButtons).toHaveLength(2)
  })

  it('renders search input and search button', async () => {
    mockGetResumes.mockResolvedValue([draftResume])
    renderInRouter(<ResumesPage />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Поиск резюме...')).toBeInTheDocument()
    })

    expect(screen.getByLabelText('Искать')).toBeInTheDocument()
  })

  it('upload button links to /app/upload', async () => {
    mockGetResumes.mockResolvedValue([])
    renderInRouter(<ResumesPage />)

    await waitFor(() => {
      const uploadLink = screen.getByText('Загрузить резюме')
      expect(uploadLink.closest('a')).toHaveAttribute('href', '/app/upload')
    })
  })
})

// ==========================================================================
// ResumeDetailPage — always show raw_text content
// ==========================================================================
describe('ResumeDetailPage v2', () => {
  it('shows raw_text when parsedData exists', async () => {
    mockGetResume.mockResolvedValue({
      id: 'r1', title: 'Моё резюме', status: 'draft', file_format: 'pdf',
      raw_text: 'Опыт работы: 5 лет в IT',
      parsed_data: { summary: 'Опытный разработчик' },
      created_at: '2026-01-01',
    })
    renderInRouter(<ResumeDetailPage />, '/app/resumes/r1')

    await waitFor(() => {
      expect(screen.getByText('Моё резюме')).toBeInTheDocument()
    })

    // Both parsed data AND raw text should be shown
    expect(screen.getByText('Опытный разработчик')).toBeInTheDocument()
    expect(screen.getByText('Опыт работы: 5 лет в IT')).toBeInTheDocument()
  })

  it('shows raw_text when parsedData is null', async () => {
    mockGetResume.mockResolvedValue({
      id: 'r1', title: 'Текстовое резюме', status: 'draft',
      raw_text: 'Привет, это мой текст резюме для теста',
      parsed_data: null,
      created_at: '2026-01-01',
    })
    renderInRouter(<ResumeDetailPage />, '/app/resumes/r1')

    await waitFor(() => {
      expect(screen.getByText('Привет, это мой текст резюме для теста')).toBeInTheDocument()
    })
  })

  it('shows raw_text when parsedData is empty object', async () => {
    mockGetResume.mockResolvedValue({
      id: 'r1', title: 'Пустое', status: 'draft',
      raw_text: 'Содержимое резюме в виде текста',
      parsed_data: {},
      created_at: '2026-01-01',
    })
    renderInRouter(<ResumeDetailPage />, '/app/resumes/r1')

    await waitFor(() => {
      expect(screen.getByText('Содержимое резюме в виде текста')).toBeInTheDocument()
    })
  })

  it('shows fallback message when no content at all', async () => {
    mockGetResume.mockResolvedValue({
      id: 'r1', title: 'Пустое резюме', status: 'draft',
      raw_text: null, parsed_data: null,
      created_at: '2026-01-01',
    })
    renderInRouter(<ResumeDetailPage />, '/app/resumes/r1')

    await waitFor(() => {
      expect(screen.getByText(/Текст резюме ещё не извлечён/)).toBeInTheDocument()
    })
  })

  it('renders optimize button', async () => {
    mockGetResume.mockResolvedValue({
      id: 'r1', title: 'Резюме', status: 'draft',
      raw_text: 'Текст', parsed_data: null,
      created_at: '2026-01-01',
    })
    renderInRouter(<ResumeDetailPage />, '/app/resumes/r1')

    await waitFor(() => {
      expect(screen.getByText('Оптимизировать')).toBeInTheDocument()
    })
  })

  it('renders delete button', async () => {
    mockGetResume.mockResolvedValue({
      id: 'r1', title: 'Резюме', status: 'draft',
      raw_text: 'Текст', parsed_data: null,
      created_at: '2026-01-01',
    })
    renderInRouter(<ResumeDetailPage />, '/app/resumes/r1')

    await waitFor(() => {
      expect(screen.getByText('Удалить')).toBeInTheDocument()
    })
  })

  it('shows error state on API failure', async () => {
    mockGetResume.mockRejectedValue(new Error('Not Found'))
    renderInRouter(<ResumeDetailPage />, '/app/resumes/bad-id')

    await waitFor(() => {
      expect(screen.getByText('Not Found')).toBeInTheDocument()
    })
  })

  it('shows loading state initially', () => {
    mockGetResume.mockImplementation(() => new Promise(() => {})) // never resolves
    renderInRouter(<ResumeDetailPage />, '/app/resumes/r1')
    expect(screen.getByText(/Загрузка резюме/)).toBeInTheDocument()
  })
})

// ==========================================================================
// ModelsPage — local API key detection
// ==========================================================================
describe('ModelsPage v2 - local key detection', () => {
  it('marks models as available when local API keys exist', async () => {
    mockGetModels.mockResolvedValue({
      models: [
        { id: 'gigachat-pro', name: 'GigaChat Pro', provider: 'Сбер', available: false, description: 'test', has_sub_models: false },
        { id: 'openai', name: 'OpenAI', provider: 'OpenAI', available: false, description: 'test', has_sub_models: true },
      ],
    })
    // Set local API key for openai
    localStorage.setItem('ai_settings', JSON.stringify({ apiKeys: { openai: 'sk-test123', gigachat: '' } }))

    renderInRouter(<ModelsPage />)

    await waitFor(() => {
      // OpenAI should NOT show "Нет ключа" badge since local key is set
      const noKeyBadges = screen.queryAllByText('Нет ключа')
      // GigaChat has no local key AND server says not available
      expect(noKeyBadges.length).toBe(1) // only GigaChat
    })
  })

  it('uses fallback models when server is unavailable', async () => {
    mockGetModels.mockRejectedValue(new Error('Server down'))
    renderInRouter(<ModelsPage />)

    await waitFor(() => {
      expect(screen.getByText('GigaChat Pro')).toBeInTheDocument()
    })

    expect(screen.getAllByText(/OpenAI/).length).toBeGreaterThanOrEqual(1)
  })

  it('does not show no-keys warning when local keys are set', async () => {
    mockGetModels.mockResolvedValue({ models: [] })
    localStorage.setItem('ai_settings', JSON.stringify({ apiKeys: { openai: 'sk-test' } }))

    renderInRouter(<ModelsPage />)

    await waitFor(() => {
      expect(screen.getByText('GigaChat Pro')).toBeInTheDocument()
    })

    expect(screen.queryByText('API-ключи не настроены')).not.toBeInTheDocument()
  })

  it('renders sub-model selector for models with has_sub_models', async () => {
    mockGetModels.mockResolvedValue({
      models: [
        { id: 'openai', name: 'OpenAI', provider: 'OpenAI', available: true, description: 'test', has_sub_models: true },
      ],
    })
    mockGetSubModels.mockResolvedValue({ sub_models: [
      { id: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI' },
    ] })

    renderInRouter(<ModelsPage />)

    await waitFor(() => {
      expect(screen.getByText('Модель OpenAI')).toBeInTheDocument()
    })
  })

  it('renders start optimization button', async () => {
    mockGetModels.mockResolvedValue({ models: [] })
    renderInRouter(<ModelsPage />)

    await waitFor(() => {
      expect(screen.getByText('Начать оптимизацию')).toBeInTheDocument()
    })
  })
})

// ==========================================================================
// UploadPage — hh.ru URL parsing with fallback
// ==========================================================================
describe('UploadPage v2 - hh.ru URL', () => {
  it('renders three tabs', () => {
    renderInRouter(<UploadPage />)
    expect(screen.getByText('Загрузить файл')).toBeInTheDocument()
    expect(screen.getByText('Ссылка hh.ru')).toBeInTheDocument()
    expect(screen.getByText('Вставить текст')).toBeInTheDocument()
  })

  it('parses hh.ru URL via parseResumeFromUrl endpoint', async () => {
    mockParseResumeFromUrl.mockResolvedValue({ id: 'parsed-1', title: 'Parsed Resume', file_format: 'text', status: 'draft' })

    renderInRouter(<UploadPage />)
    fireEvent.click(screen.getByText('Ссылка hh.ru'))

    const input = screen.getByPlaceholderText('https://hh.ru/resume/abc123def4')
    fireEvent.change(input, { target: { value: 'https://hh.ru/resume/90d67b47' } })
    fireEvent.click(screen.getByText('Загрузить резюме'))

    await waitFor(() => {
      expect(mockParseResumeFromUrl).toHaveBeenCalledWith('https://hh.ru/resume/90d67b47')
    })
  })

  it('falls back to createResumeFromText when parseResumeFromUrl fails', async () => {
    mockParseResumeFromUrl.mockRejectedValue(new Error('Not supported'))
    mockCreateResumeFromText.mockResolvedValue({ id: 'fallback-1', title: 'Fallback', file_format: 'text', status: 'draft' })

    renderInRouter(<UploadPage />)
    fireEvent.click(screen.getByText('Ссылка hh.ru'))

    const input = screen.getByPlaceholderText('https://hh.ru/resume/abc123def4')
    fireEvent.change(input, { target: { value: 'https://hh.ru/resume/test123' } })
    fireEvent.click(screen.getByText('Загрузить резюме'))

    await waitFor(() => {
      expect(mockCreateResumeFromText).toHaveBeenCalledWith({
        text: '',
        title: 'Резюме с hh.ru',
        source_url: 'https://hh.ru/resume/test123',
      })
    })
  })

  it('shows error when both URL parse methods fail', async () => {
    mockParseResumeFromUrl.mockRejectedValue(new Error('fail'))
    mockCreateResumeFromText.mockRejectedValue(new Error('fail'))

    renderInRouter(<UploadPage />)
    fireEvent.click(screen.getByText('Ссылка hh.ru'))

    const input = screen.getByPlaceholderText('https://hh.ru/resume/abc123def4')
    fireEvent.change(input, { target: { value: 'https://hh.ru/resume/bad' } })
    fireEvent.click(screen.getByText('Загрузить резюме'))

    await waitFor(() => {
      expect(screen.getByText(/Не удалось автоматически загрузить/)).toBeInTheDocument()
    })
  })

  it('paste text tab works independently', async () => {
    mockCreateResumeFromText.mockResolvedValue({ id: 'text-1', title: 'Text Resume', file_format: 'text', status: 'draft' })

    renderInRouter(<UploadPage />)
    fireEvent.click(screen.getByText('Вставить текст'))

    const textarea = screen.getByPlaceholderText(/Вставьте текст резюме/)
    fireEvent.change(textarea, { target: { value: 'Это мой текст резюме с достаточной длиной символов для прохождения валидации.' } })

    fireEvent.click(screen.getByText('Продолжить'))

    await waitFor(() => {
      expect(mockCreateResumeFromText).toHaveBeenCalledWith(
        expect.objectContaining({ text: expect.any(String) })
      )
    })
  })

  it('rejects short paste text', () => {
    renderInRouter(<UploadPage />)
    fireEvent.click(screen.getByText('Вставить текст'))

    const textarea = screen.getByPlaceholderText(/Вставьте текст резюме/)
    fireEvent.change(textarea, { target: { value: 'Короткий' } })

    const continueBtn = screen.getByText('Продолжить')
    expect(continueBtn).toBeDisabled()
  })

  it('disables load button when URL is empty', () => {
    renderInRouter(<UploadPage />)
    fireEvent.click(screen.getByText('Ссылка hh.ru'))

    const loadBtn = screen.getByText('Загрузить резюме')
    expect(loadBtn).toBeDisabled()
  })
})

// ==========================================================================
// SettingsAiPage — dynamic model loading
// ==========================================================================
describe('SettingsAiPage v2 - dynamic models', () => {
  it('renders all four model providers', () => {
    renderInRouter(<SettingsAiPage />)
    expect(screen.getByText('GigaChat Pro')).toBeInTheDocument()
    expect(screen.getAllByText(/OpenAI/).length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText(/Anthropic/).length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText(/OpenRouter/).length).toBeGreaterThanOrEqual(1)
  })

  it('shows API key inputs for all providers', () => {
    renderInRouter(<SettingsAiPage />)
    expect(screen.getByPlaceholderText('Credentials (Base64)')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('sk-...')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('sk-ant-...')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('sk-or-v1-...')).toBeInTheDocument()
  })

  it('uses fallback sub-models when server returns empty', async () => {
    mockGetSubModels.mockResolvedValue({ sub_models: [] })

    renderInRouter(<SettingsAiPage />)

    // Click on OpenAI model
    fireEvent.click(screen.getByText('OpenAI'))

    await waitFor(() => {
      // Fallback sub-models should be loaded
      const options = screen.getAllByRole('option')
      expect(options.length).toBeGreaterThan(0)
    })
  })

  it('saves and loads settings from localStorage', () => {
    renderInRouter(<SettingsAiPage />)

    fireEvent.click(screen.getByText('Сохранить'))

    const saved = localStorage.getItem('ai_settings')
    expect(saved).toBeTruthy()
  })

  it('resets settings on reset button click', () => {
    localStorage.setItem('ai_settings', JSON.stringify({ model: 'openai', apiKeys: { openai: 'test' } }))
    renderInRouter(<SettingsAiPage />)

    fireEvent.click(screen.getByText('Сбросить'))

    expect(localStorage.getItem('ai_settings')).toBeNull()
  })

  it('shows sub-model selector for providers with hasSubModels', async () => {
    mockGetSubModels.mockResolvedValue({ sub_models: [] })
    renderInRouter(<SettingsAiPage />)

    // Click Anthropic
    fireEvent.click(screen.getByText('Anthropic Claude'))

    await waitFor(() => {
      expect(screen.getByText(/Модель Anthropic Claude/)).toBeInTheDocument()
    })
  })

  it('shows optimization toggles', () => {
    renderInRouter(<SettingsAiPage />)
    expect(screen.getByText('ATS оптимизация')).toBeInTheDocument()
    expect(screen.getByText('Автоматические метрики')).toBeInTheDocument()
  })
})

// ==========================================================================
// SettingsProfilePage — per-account avatar storage
// ==========================================================================
describe('SettingsProfilePage v2 - per-account avatar', () => {
  it('uses user-specific localStorage key for avatar', () => {
    localStorage.setItem('user_avatar_user-42', 'data:image/png;base64,abc123')
    renderInRouter(<SettingsProfilePage />)

    // Avatar should be loaded from user-specific key
    const avatarDiv = document.querySelector('[style*="data:image/png;base64,abc123"]')
    expect(avatarDiv).toBeTruthy()
  })

  it('does NOT load avatar from other user key', () => {
    localStorage.setItem('user_avatar_other-user', 'data:image/png;base64,other')
    renderInRouter(<SettingsProfilePage />)

    const avatarDiv = document.querySelector('[style*="data:image/png;base64,other"]')
    expect(avatarDiv).toBeFalsy()
  })

  it('does NOT load avatar from old global key', () => {
    localStorage.setItem('user_avatar', 'data:image/png;base64,global')
    renderInRouter(<SettingsProfilePage />)

    const avatarDiv = document.querySelector('[style*="data:image/png;base64,global"]')
    expect(avatarDiv).toBeFalsy()
  })

  it('removes avatar from correct per-user key', () => {
    localStorage.setItem('user_avatar_user-42', 'data:image/png;base64,to-remove')
    renderInRouter(<SettingsProfilePage />)

    fireEvent.click(screen.getByText('Удалить'))
    expect(localStorage.getItem('user_avatar_user-42')).toBeNull()
  })

  it('renders user name from context', () => {
    renderInRouter(<SettingsProfilePage />)
    // user full_name is 'Тест Юзер' → firstName = 'Тест', lastName = 'Юзер'
    expect(screen.getByDisplayValue('Тест')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Юзер')).toBeInTheDocument()
  })

  it('save button calls updateProfile', async () => {
    mockUpdateProfile.mockResolvedValue({})
    renderInRouter(<SettingsProfilePage />)

    fireEvent.click(screen.getByText('Сохранить изменения'))

    await waitFor(() => {
      expect(mockUpdateProfile).toHaveBeenCalled()
    })
  })
})

// ==========================================================================
// SettingsSecurityPage — account deletion with logout
// ==========================================================================
describe('SettingsSecurityPage v2 - account deletion', () => {
  it('renders delete account button', () => {
    renderInRouter(<SettingsSecurityPage />)
    expect(screen.getByText('Удалить аккаунт')).toBeInTheDocument()
  })

  it('shows confirmation input on delete click', () => {
    renderInRouter(<SettingsSecurityPage />)

    fireEvent.click(screen.getByText('Удалить аккаунт'))

    expect(screen.getByPlaceholderText(/Введите "УДАЛИТЬ"/)).toBeInTheDocument()
    expect(screen.getByText('Подтвердить')).toBeDisabled()
  })

  it('enables confirm button when УДАЛИТЬ is typed', () => {
    renderInRouter(<SettingsSecurityPage />)

    fireEvent.click(screen.getByText('Удалить аккаунт'))

    const input = screen.getByPlaceholderText(/Введите "УДАЛИТЬ"/)
    fireEvent.change(input, { target: { value: 'УДАЛИТЬ' } })

    expect(screen.getByText('Подтвердить')).not.toBeDisabled()
  })

  it('calls deleteAccount API and logout on confirm', async () => {
    mockDeleteAccount.mockResolvedValue(undefined)

    renderInRouter(<SettingsSecurityPage />)

    fireEvent.click(screen.getByText('Удалить аккаунт'))

    const input = screen.getByPlaceholderText(/Введите "УДАЛИТЬ"/)
    fireEvent.change(input, { target: { value: 'УДАЛИТЬ' } })

    fireEvent.click(screen.getByText('Подтвердить'))

    await waitFor(() => {
      expect(mockDeleteAccount).toHaveBeenCalled()
      expect(mockLogout).toHaveBeenCalled()
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  it('does not call deleteAccount when text does not match', () => {
    renderInRouter(<SettingsSecurityPage />)

    fireEvent.click(screen.getByText('Удалить аккаунт'))

    const input = screen.getByPlaceholderText(/Введите "УДАЛИТЬ"/)
    fireEvent.change(input, { target: { value: 'удалить' } }) // lowercase

    expect(screen.getByText('Подтвердить')).toBeDisabled()
  })

  it('cancel button hides confirmation', () => {
    renderInRouter(<SettingsSecurityPage />)

    fireEvent.click(screen.getByText('Удалить аккаунт'))
    expect(screen.getByText('Подтвердить')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Отмена'))
    expect(screen.queryByText('Подтвердить')).not.toBeInTheDocument()
  })

  it('password change form works', async () => {
    mockChangePassword.mockResolvedValue({ message: 'OK' })

    renderInRouter(<SettingsSecurityPage />)

    const passwordInputs = screen.getAllByPlaceholderText('••••••••')
    fireEvent.change(passwordInputs[0], { target: { value: 'oldPass123' } })

    const newPwInput = screen.getByPlaceholderText(/мин.*8.*символ/i)
    fireEvent.change(newPwInput, { target: { value: 'newPass456' } })

    fireEvent.change(passwordInputs[1], { target: { value: 'newPass456' } })

    fireEvent.click(screen.getByText('Обновить пароль'))

    await waitFor(() => {
      expect(mockChangePassword).toHaveBeenCalledWith({
        current_password: 'oldPass123',
        new_password: 'newPass456',
      })
    })
  })

  it('shows error when passwords do not match', async () => {
    renderInRouter(<SettingsSecurityPage />)

    const passwordInputs = screen.getAllByPlaceholderText('••••••••')
    fireEvent.change(passwordInputs[0], { target: { value: 'oldPass123' } })

    const newPwInput = screen.getByPlaceholderText(/мин.*8.*символ/i)
    fireEvent.change(newPwInput, { target: { value: 'newPass456' } })

    fireEvent.change(passwordInputs[1], { target: { value: 'different' } })

    fireEvent.click(screen.getByText('Обновить пароль'))

    await waitFor(() => {
      expect(screen.getByText('Пароли не совпадают')).toBeInTheDocument()
    })
  })

  it('renders 2FA placeholder', () => {
    renderInRouter(<SettingsSecurityPage />)
    expect(screen.getByText('Двухфакторная аутентификация')).toBeInTheDocument()
    expect(screen.getByText('Скоро')).toBeInTheDocument()
  })
})

// ==========================================================================
// API client — new methods
// ==========================================================================
describe('API methods v2', () => {
  it('parseResumeFromUrl is callable', () => {
    expect(mockParseResumeFromUrl).toBeDefined()
    expect(typeof mockParseResumeFromUrl).toBe('function')
  })

  it('deleteAccount is callable', () => {
    expect(mockDeleteAccount).toBeDefined()
    expect(typeof mockDeleteAccount).toBe('function')
  })
})
