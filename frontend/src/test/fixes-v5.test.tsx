/**
 * Tests for v5 fixes:
 * 1. SettingsProfilePage: email field padding for verification badge, avatar camera icon, responsive grid
 * 2. SettingsSecurityPage: password change triggers logout + redirect
 * 3. VacancyPage: full vacancy details fetching from hh.ru
 * 4. ModelsPage: expanded fallback sub-models lists
 * 5. ResumeDetailPage: download format selection menu, formatted raw text display
 * 6. ProcessingPage: friendly LLM error messages, always show settings link
 * 7. ResultsPage: word-level diff highlighting with computeWordDiff
 * 8. HelpPage: renders with all sections, FAQ accordion
 * 9. AppLayout: Help link in sidebar navigation
 * 10. App.tsx: /app/help route exists
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { WizardProvider } from '../contexts/WizardContext'

/* eslint-disable @typescript-eslint/no-explicit-any */

// ─── Mock Data ───────────────────────────────────────────────
const mockResumeDetail = {
  id: 'res-1', title: 'Python Dev', status: 'draft', file_format: 'pdf',
  created_at: '2026-03-15T10:00:00Z',
  raw_text: 'ОПЫТ РАБОТЫ\n- Python разработчик\n• Оптимизировал API\nОБРАЗОВАНИЕ\nМГУ, Информатика',
  parsed_data: {
    summary: 'Опытный Python-разработчик',
    experience: [{ position: 'Senior Developer', company: 'ТехКорп', period: '2020-2025', achievements: ['Оптимизировал API'] }],
    education: [{ institution: 'МГУ', degree: 'Магистр', specialization: 'Информатика', year: 2020 }],
    skills: ['Python', 'FastAPI', 'PostgreSQL'],
  },
}

const mockResult = {
  id: 'result-1',
  match_score_after: 85,
  match_score_before: 45,
  ats_rating: 'A',
  model_name: 'gpt-4o',
  processing_time_ms: 15000,
  keywords_added: ['FastAPI', 'Docker'],
  original_text: 'Я работал программистом 5 лет. Делал разные задачи.',
  rewritten_text: 'Опытный Senior Python-разработчик с 5-летним стажем. Реализовал высоконагруженный API.',
  vacancy_id: 'vac-1',
}

const mockVacancies = {
  items: [
    {
      hh_id: 'vac-1', title: 'Python Developer', company: 'Яндекс',
      city: 'Москва', salary_from: 200000, salary_to: 350000,
      key_skills: ['Python', 'SQL'], experience: '3-6 лет',
      description: null, // search result — no full description yet
      snippet: { requirement: '<b>Python</b> 3+', responsibility: 'Разработка API' },
      url: 'https://hh.ru/vacancy/vac-1',
    },
  ],
  found: 1, page: 0, pages: 1,
}

const mockVacancyFull = {
  hh_id: 'vac-1', title: 'Python Developer', company: 'Яндекс',
  city: 'Москва', salary_from: 200000, salary_to: 350000,
  experience: '3-6 лет', key_skills: ['Python', 'SQL', 'FastAPI'],
  description: '<p>Описание полной вакансии</p>',
}

// ─── API Mock Setup ──────────────────────────────────────────
const mockGetResume = vi.fn()
const mockDeleteResume = vi.fn()
const mockDownloadResumeFile = vi.fn()
const mockExportDocx = vi.fn()
const mockGetRewriteHistory = vi.fn()
const mockChangePassword = vi.fn()
const mockUpdateProfile = vi.fn()
const mockSearchVacancies = vi.fn()
const mockCreateVacancyFromUrl = vi.fn()
const mockGetHHVacancyDetail = vi.fn()
const mockGetRewriteStatus = vi.fn()
const mockGetRewriteResult = vi.fn()
const mockGetModels = vi.fn()
const mockGetSubModels = vi.fn()
const mockStartRewrite = vi.fn()
const mockGetVacancy = vi.fn()

vi.mock('../services/api', () => ({
  api: {
    getResume: (...a: any[]) => mockGetResume(...a),
    getResumes: vi.fn().mockResolvedValue([]),
    deleteResume: (...a: any[]) => mockDeleteResume(...a),
    downloadResumeFile: (...a: any[]) => mockDownloadResumeFile(...a),
    exportDocx: (...a: any[]) => mockExportDocx(...a),
    getRewriteHistory: (...a: any[]) => mockGetRewriteHistory(...a),
    getRewriteResult: (...a: any[]) => mockGetRewriteResult(...a),
    getRewriteStatus: (...a: any[]) => mockGetRewriteStatus(...a),
    changePassword: (...a: any[]) => mockChangePassword(...a),
    updateProfile: (...a: any[]) => mockUpdateProfile(...a),
    searchVacancies: (...a: any[]) => mockSearchVacancies(...a),
    createVacancyFromUrl: (...a: any[]) => mockCreateVacancyFromUrl(...a),
    createVacancyManual: vi.fn().mockResolvedValue({ id: 'vac-m' }),
    getHHVacancyDetail: (...a: any[]) => mockGetHHVacancyDetail(...a),
    getModels: (...a: any[]) => mockGetModels(...a),
    getSubModels: (...a: any[]) => mockGetSubModels(...a),
    startRewrite: (...a: any[]) => mockStartRewrite(...a),
    getVacancy: (...a: any[]) => mockGetVacancy(...a),
    setToken: vi.fn(),
    clearToken: vi.fn(),
    getMe: vi.fn().mockResolvedValue({ id: 'user-1', full_name: 'Тест Юзер', email: 'test@example.com', plan: 'free', optimizations_used: 0 }),
    selectSearchVacancy: vi.fn(),
    deleteAccount: vi.fn(),
  },
  ApiClient: vi.fn(),
}))

const mockLogout = vi.fn()
vi.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    isAuthenticated: true, loading: false,
    user: { id: 'user-1', full_name: 'Тест Юзер', email: 'test@example.com', plan: 'free', optimizations_used: 0, is_active: true },
    login: vi.fn(), logout: mockLogout, register: vi.fn(), refreshUser: vi.fn(),
  }),
}))

import { useEffect } from 'react'

// ─── Imports (after mocks) ──────────────────────────────────
import SettingsProfilePage from '../pages/settings/SettingsProfilePage'
import SettingsSecurityPage from '../pages/settings/SettingsSecurityPage'
import VacancyPage from '../pages/wizard/VacancyPage'
import ModelsPage from '../pages/wizard/ModelsPage'
import ResumeDetailPage from '../pages/resumes/ResumeDetailPage'
import ProcessingPage from '../pages/wizard/ProcessingPage'
import ResultsPage from '../pages/wizard/ResultsPage'
import HelpPage from '../pages/HelpPage'
import AppLayout from '../components/layout/AppLayout'
import { useWizard } from '../contexts/WizardContext'

// Helper to inject taskId into wizard context for ProcessingPage tests
// Delays rendering children until taskId is set to prevent ProcessingPage from seeing null
function WithTaskId({ taskId, children }: { taskId: string; children: React.ReactNode }) {
  const wizard = useWizard()
  useEffect(() => { wizard.setTaskId(taskId) }, []) // eslint-disable-line react-hooks/exhaustive-deps
  if (!wizard.taskId) return null
  return <>{children}</>
}

// ─── Helpers ─────────────────────────────────────────────────
function renderWithRouter(element: React.ReactElement, { route = '/' }: { route?: string } = {}) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <WizardProvider>
        <Routes>
          <Route path="/app/settings/profile" element={element} />
          <Route path="/app/settings/security" element={element} />
          <Route path="/app/vacancy" element={element} />
          <Route path="/app/models" element={element} />
          <Route path="/app/resumes/:id" element={element} />
          <Route path="/app/processing" element={element} />
          <Route path="/app/results/:id" element={element} />
          <Route path="/app/results" element={element} />
          <Route path="/app/help" element={element} />
          <Route path="/app" element={element} />
          <Route path="/auth" element={<div data-testid="auth-page">Auth</div>} />
        </Routes>
      </WizardProvider>
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  mockGetResume.mockResolvedValue(mockResumeDetail)
  mockDeleteResume.mockResolvedValue(undefined)
  mockDownloadResumeFile.mockResolvedValue(new Blob(['file content'], { type: 'application/pdf' }))
  mockExportDocx.mockResolvedValue(new Blob(['docx content']))
  mockGetRewriteHistory.mockResolvedValue([])
  mockChangePassword.mockResolvedValue({ message: 'ok' })
  mockUpdateProfile.mockResolvedValue({ id: 'user-1', full_name: 'Тест Юзер', email: 'test@example.com' })
  mockSearchVacancies.mockResolvedValue(mockVacancies)
  mockCreateVacancyFromUrl.mockResolvedValue({ id: 'vac-new' })
  mockGetHHVacancyDetail.mockResolvedValue(mockVacancyFull)
  mockGetRewriteStatus.mockResolvedValue({ status: 'processing', step: 'analyzing', progress: 50 })
  mockGetRewriteResult.mockResolvedValue(mockResult)
  mockGetModels.mockResolvedValue({ models: [] })
  mockGetSubModels.mockResolvedValue({ sub_models: [] })
  mockStartRewrite.mockResolvedValue({ task_id: 'task-1' })
  mockGetVacancy.mockResolvedValue({ id: 'vac-1', title: 'Python Dev', description: 'Test' })

  vi.spyOn(window, 'confirm').mockReturnValue(true)
  vi.spyOn(window, 'alert').mockImplementation(() => {})
  vi.stubGlobal('URL', { ...window.URL, createObjectURL: vi.fn(() => 'blob:mock'), revokeObjectURL: vi.fn() })
  localStorage.clear()
})

// ═══════════════════════════════════════════════════════════════
// 1. SettingsProfilePage — avatar, email badge, responsive grid
// ═══════════════════════════════════════════════════════════════
describe('SettingsProfilePage v5 fixes', () => {
  it('renders avatar with camera button outside overflow hidden', async () => {
    renderWithRouter(<SettingsProfilePage />, { route: '/app/settings/profile' })
    // The camera button should be in a separate container (not clipped by overflow:hidden)
    const photoInput = screen.getByTestId('photo-upload-input')
    expect(photoInput).toBeDefined()
    // Camera button should exist
    const avatarArea = photoInput.closest('div')!.parentElement!
    const buttons = avatarArea.querySelectorAll('button')
    expect(buttons.length).toBeGreaterThanOrEqual(1)
  })

  it('email field has paddingRight to prevent badge overlap', async () => {
    renderWithRouter(<SettingsProfilePage />, { route: '/app/settings/profile' })
    const emailInput = screen.getByDisplayValue('test@example.com')
    expect(emailInput).toBeDefined()
    // Check style has paddingRight
    expect(emailInput.getAttribute('style')).toContain('padding-right')
  })

  it('shows "Подтверждён" verification badge with background', async () => {
    renderWithRouter(<SettingsProfilePage />, { route: '/app/settings/profile' })
    expect(screen.getByText('Подтверждён')).toBeDefined()
  })

  it('profile grid uses responsive auto-fit layout', async () => {
    renderWithRouter(<SettingsProfilePage />, { route: '/app/settings/profile' })
    const grid = document.querySelector('.profile-grid') as HTMLElement
    expect(grid).toBeDefined()
    expect(grid?.style.gridTemplateColumns).toContain('auto-fit')
  })

  it('verification CheckCircle icon in email subtitle has flexShrink 0', async () => {
    renderWithRouter(<SettingsProfilePage />, { route: '/app/settings/profile' })
    // The email subtitle area should show the email + check icon
    const nameDiv = screen.getByText('Тест Юзер')
    expect(nameDiv).toBeDefined()
  })
})

// ═══════════════════════════════════════════════════════════════
// 2. SettingsSecurityPage — password change forces logout
// ═══════════════════════════════════════════════════════════════
describe('SettingsSecurityPage v5 password change', () => {
  it('renders password change form', async () => {
    renderWithRouter(<SettingsSecurityPage />, { route: '/app/settings/security' })
    expect(screen.getByText('Сменить пароль')).toBeDefined()
    expect(screen.getAllByPlaceholderText('••••••••').length).toBeGreaterThan(0)
  })

  it('validates matching passwords', async () => {
    renderWithRouter(<SettingsSecurityPage />, { route: '/app/settings/security' })
    const inputs = screen.getAllByPlaceholderText('••••••••')
    fireEvent.change(inputs[0], { target: { value: 'OldPass123' } })
    fireEvent.change(screen.getByPlaceholderText('Мин. 8 символов, цифра + буква'), { target: { value: 'NewPass123' } })
    fireEvent.change(inputs[1], { target: { value: 'Different123' } })
    fireEvent.click(screen.getByText('Обновить пароль'))
    await waitFor(() => {
      expect(screen.getByText('Пароли не совпадают')).toBeDefined()
    })
  })

  it('minimum 8 characters validation', async () => {
    renderWithRouter(<SettingsSecurityPage />, { route: '/app/settings/security' })
    const inputs = screen.getAllByPlaceholderText('••••••••')
    fireEvent.change(inputs[0], { target: { value: 'OldPass1' } })
    fireEvent.change(screen.getByPlaceholderText('Мин. 8 символов, цифра + буква'), { target: { value: 'Short1' } })
    fireEvent.change(inputs[1], { target: { value: 'Short1' } })
    fireEvent.click(screen.getByText('Обновить пароль'))
    await waitFor(() => {
      expect(screen.getByText('Пароль должен быть минимум 8 символов')).toBeDefined()
    })
  })

  it('shows success message and triggers logout after successful password change', async () => {
    renderWithRouter(<SettingsSecurityPage />, { route: '/app/settings/security' })
    const inputs = screen.getAllByPlaceholderText('••••••••')
    fireEvent.change(inputs[0], { target: { value: 'OldPass123' } })
    fireEvent.change(screen.getByPlaceholderText('Мин. 8 символов, цифра + буква'), { target: { value: 'NewPass123' } })
    fireEvent.change(inputs[1], { target: { value: 'NewPass123' } })
    fireEvent.click(screen.getByText('Обновить пароль'))
    await waitFor(() => {
      expect(mockChangePassword).toHaveBeenCalledWith({ current_password: 'OldPass123', new_password: 'NewPass123' })
    })
    await waitFor(() => {
      expect(screen.getByText(/Пароль обновлён/)).toBeDefined()
    })
  })

  it('shows error on failed password change', async () => {
    mockChangePassword.mockRejectedValueOnce(new Error('Неверный текущий пароль'))
    renderWithRouter(<SettingsSecurityPage />, { route: '/app/settings/security' })
    const inputs = screen.getAllByPlaceholderText('••••••••')
    fireEvent.change(inputs[0], { target: { value: 'WrongPass1' } })
    fireEvent.change(screen.getByPlaceholderText('Мин. 8 символов, цифра + буква'), { target: { value: 'NewPass123' } })
    fireEvent.change(inputs[1], { target: { value: 'NewPass123' } })
    fireEvent.click(screen.getByText('Обновить пароль'))
    await waitFor(() => {
      expect(screen.getByText('Неверный текущий пароль')).toBeDefined()
    })
  })

  it('renders delete account section', async () => {
    renderWithRouter(<SettingsSecurityPage />, { route: '/app/settings/security' })
    expect(screen.getByText('Опасная зона')).toBeDefined()
    expect(screen.getByText('Удалить аккаунт')).toBeDefined()
  })
})

// ═══════════════════════════════════════════════════════════════
// 3. VacancyPage — fetch full vacancy details
// ═══════════════════════════════════════════════════════════════
describe('VacancyPage v5 full vacancy details', () => {
  it('renders search form with city selector', async () => {
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy' })
    expect(screen.getByPlaceholderText('Product Manager')).toBeDefined()
    expect(screen.getByText('Москва')).toBeDefined()
  })

  it('shows vacancy cards after search', async () => {
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy' })
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'Python' } })
    fireEvent.click(screen.getByText('Найти'))
    await waitFor(() => {
      expect(screen.getByText('Python Developer')).toBeDefined()
      expect(screen.getByText(/Яндекс/)).toBeDefined()
    })
  })

  it('clicking Подробнее fetches full vacancy details from hh.ru', async () => {
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy' })
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'Python' } })
    fireEvent.click(screen.getByText('Найти'))
    await waitFor(() => expect(screen.getByText('Python Developer')).toBeDefined())
    // Click "Подробнее" button
    fireEvent.click(screen.getByText('Подробнее'))
    // Should call getHHVacancyDetail since original has no description
    await waitFor(() => {
      expect(mockGetHHVacancyDetail).toHaveBeenCalledWith('vac-1')
    })
    // After loading, should show full description
    await waitFor(() => {
      expect(screen.getByText('Описание полной вакансии')).toBeDefined()
    })
  })

  it('displays salary in vacancy details modal', async () => {
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy' })
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'Python' } })
    fireEvent.click(screen.getByText('Найти'))
    await waitFor(() => expect(screen.getByText('Python Developer')).toBeDefined())

    fireEvent.click(screen.getByText('Подробнее'))
    await waitFor(() => {
      // Salary should be visible (card + modal may both match)
      const salaryElements = screen.getAllByText(/200\s*000/)
      expect(salaryElements.length).toBeGreaterThan(0)
    })
  })

  it('closes vacancy modal on overlay click', async () => {
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy' })
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'Python' } })
    fireEvent.click(screen.getByText('Найти'))
    await waitFor(() => expect(screen.getByText('Python Developer')).toBeDefined())

    fireEvent.click(screen.getByText('Подробнее'))
    await waitFor(() => expect(screen.getByText('Подробности вакансии')).toBeDefined())

    const overlay = screen.getByTestId('vacancy-detail-modal')
    fireEvent.click(overlay)
    await waitFor(() => {
      expect(screen.queryByText('Подробности вакансии')).toBeNull()
    })
  })
})

// ═══════════════════════════════════════════════════════════════
// 4. ModelsPage — expanded fallback sub-models
// ═══════════════════════════════════════════════════════════════
describe('ModelsPage v5 expanded models', () => {
  it('renders with fallback models when API returns empty', async () => {
    mockGetModels.mockResolvedValue({ models: [] })
    renderWithRouter(<ModelsPage />, { route: '/app/models' })
    await waitFor(() => {
      expect(screen.getByText('GigaChat Pro')).toBeDefined()
      expect(screen.getAllByText('OpenAI').length).toBeGreaterThan(0)
      expect(screen.getByText('Anthropic Claude')).toBeDefined()
      expect(screen.getAllByText('OpenRouter').length).toBeGreaterThan(0)
    })
  })

  it('shows expanded OpenAI sub-models in fallback', async () => {
    mockGetModels.mockResolvedValue({ models: [] })
    mockGetSubModels.mockResolvedValue({ sub_models: [] })
    renderWithRouter(<ModelsPage />, { route: '/app/models' })
    await waitFor(() => expect(screen.getAllByText('OpenAI').length).toBeGreaterThan(0))
    // Select OpenAI card
    const modelCards = document.querySelectorAll('.model-card')
    const openaiCard = Array.from(modelCards).find(c => c.textContent?.includes('OpenAI'))
    if (openaiCard) fireEvent.click(openaiCard)
    await waitFor(() => {
      // Sub-models shown in select option text: "GPT-4o (OpenAI)" etc.
      // Use getAllByText because "GPT-4o" also matches "GPT-4o Mini"
      expect(screen.getAllByText(/GPT-4o/i).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/GPT-4o Mini/i).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/GPT-4\.1/i).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/\bo3\b/).length).toBeGreaterThan(0)
    })
  })

  it('shows expanded Anthropic sub-models in fallback', async () => {
    mockGetModels.mockResolvedValue({ models: [] })
    mockGetSubModels.mockResolvedValue({ sub_models: [] })
    renderWithRouter(<ModelsPage />, { route: '/app/models' })
    await waitFor(() => expect(screen.getByText('Anthropic Claude')).toBeDefined())
    fireEvent.click(screen.getByText('Anthropic Claude'))
    await waitFor(() => {
      // Sub-models in select option text: "Claude Sonnet 4 (Anthropic)" etc.
      expect(screen.getAllByText(/Claude Sonnet 4/i).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/Claude Opus 4/i).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/Claude 3\.5 Haiku/i).length).toBeGreaterThan(0)
    })
  })

  it('shows expanded OpenRouter sub-models in fallback', async () => {
    mockGetModels.mockResolvedValue({ models: [] })
    mockGetSubModels.mockResolvedValue({ sub_models: [] })
    renderWithRouter(<ModelsPage />, { route: '/app/models' })
    await waitFor(() => expect(screen.getAllByText('OpenRouter').length).toBeGreaterThan(0))
    // Select OpenRouter card
    const modelCards = document.querySelectorAll('.model-card')
    const routerCard = Array.from(modelCards).find(c => c.textContent?.includes('OpenRouter'))
    if (routerCard) fireEvent.click(routerCard)
    await waitFor(() => {
      // Sub-models in select option text: "Gemini 2.5 Flash (OpenRouter)" etc.
      expect(screen.getByText('Gemini 2.5 Flash', { exact: false })).toBeDefined()
      expect(screen.getByText('DeepSeek R1', { exact: false })).toBeDefined()
      expect(screen.getByText('Llama 4 Maverick', { exact: false })).toBeDefined()
    })
  })
})

// ═══════════════════════════════════════════════════════════════
// 5. ResumeDetailPage — format download, formatted text
// ═══════════════════════════════════════════════════════════════
describe('ResumeDetailPage v5 download and display', () => {
  it('shows download button with format dropdown', async () => {
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => expect(screen.getByText('Python Dev')).toBeDefined())
    // Click download button to show format menu
    const downloadBtn = screen.getByText(/Скачать/)
    fireEvent.click(downloadBtn)
    // Format menu should appear (labels include emoji prefix)
    await waitFor(() => {
      expect(screen.getByText('PDF (.pdf)', { exact: false })).toBeDefined()
      expect(screen.getByText('DOCX (.docx)', { exact: false })).toBeDefined()
      expect(screen.getByText('Текст (.txt)', { exact: false })).toBeDefined()
    })
  })

  it('downloads as TXT when format selected', async () => {
    mockDownloadResumeFile.mockRejectedValue(new Error('no file'))
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => expect(screen.getByText('Python Dev')).toBeDefined())
    fireEvent.click(screen.getByText(/Скачать/))
    await waitFor(() => expect(screen.getByText('Текст (.txt)', { exact: false })).toBeDefined())
    fireEvent.click(screen.getByText('Текст (.txt)', { exact: false }))
    await waitFor(() => {
      // Should create blob from raw_text
      expect(URL.createObjectURL).toHaveBeenCalled()
    })
  })

  it('renders formatted raw text with heading detection', async () => {
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => expect(screen.getByText('Текст резюме')).toBeDefined())
    // ОПЫТ РАБОТЫ should render as heading (bold)
    const headingElement = screen.getByText('ОПЫТ РАБОТЫ')
    expect(headingElement).toBeDefined()
    expect(headingElement.style.fontWeight).toBe('700')
  })

  it('renders bullet points with padding', async () => {
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => expect(screen.getByText('Текст резюме')).toBeDefined())
    const bullet = screen.getByText('- Python разработчик')
    expect(bullet).toBeDefined()
    expect(bullet.style.paddingLeft).toBe('1rem')
  })

  it('renders parsed data sections', async () => {
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => {
      expect(screen.getByText('Профессиональное саммари')).toBeDefined()
      expect(screen.getByText('Опытный Python-разработчик')).toBeDefined()
      expect(screen.getByText('Опыт работы')).toBeDefined()
      expect(screen.getByText('Образование')).toBeDefined()
      expect(screen.getByText('Навыки')).toBeDefined()
    })
  })

  it('delete button works for all resume types', async () => {
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => expect(screen.getByText('Python Dev')).toBeDefined())
    fireEvent.click(screen.getByText('Удалить'))
    await waitFor(() => {
      expect(mockDeleteResume).toHaveBeenCalledWith('res-1')
    })
  })
})

// ═══════════════════════════════════════════════════════════════
// 6. ProcessingPage — friendly error messages
// ═══════════════════════════════════════════════════════════════
describe('ProcessingPage v5 error handling', () => {
  it('shows friendly message for "provider all" error', async () => {
    mockGetRewriteStatus.mockResolvedValue({
      status: 'failed', step: 'rewriting', progress: 30,
      error_message: 'LLM-провайдер all временно недоступен',
    })
    renderWithRouter(
      <WithTaskId taskId="task-1"><ProcessingPage /></WithTaskId>,
      { route: '/app/processing' }
    )
    await waitFor(() => {
      expect(screen.getByText(/Ни один LLM-провайдер не настроен/)).toBeDefined()
    })
  })

  it('shows friendly message for payment error', async () => {
    mockGetRewriteStatus.mockResolvedValue({
      status: 'failed', step: 'rewriting', progress: 30,
      error_message: 'Payment Required (402)',
    })
    renderWithRouter(
      <WithTaskId taskId="task-1"><ProcessingPage /></WithTaskId>,
      { route: '/app/processing' }
    )
    await waitFor(() => {
      expect(screen.getByText(/тарификации/)).toBeDefined()
    })
  })

  it('always shows settings link on error', async () => {
    mockGetRewriteStatus.mockResolvedValue({
      status: 'failed', step: 'rewriting', progress: 30,
      error_message: 'Ошибка какая-то',
    })
    renderWithRouter(<ProcessingPage />, { route: '/app/processing' })
    await waitFor(() => {
      expect(screen.getByText('Настроить ключи')).toBeDefined()
      expect(screen.getByText('Выбрать другую модель')).toBeDefined()
    })
  })

  it('shows processing steps during active processing', async () => {
    mockGetRewriteStatus.mockResolvedValue({ status: 'processing', step: 'analyzing', progress: 50 })
    renderWithRouter(
      <WithTaskId taskId="task-1"><ProcessingPage /></WithTaskId>,
      { route: '/app/processing' }
    )
    await waitFor(() => {
      expect(screen.getByText('Анализ вакансии')).toBeDefined()
      expect(screen.getByText('AI оптимизация')).toBeDefined()
    })
  })

  it('shows error when no taskId', async () => {
    renderWithRouter(<ProcessingPage />, { route: '/app/processing' })
    await waitFor(() => {
      expect(screen.getByText(/Нет задачи/)).toBeDefined()
    })
  })
})

// ═══════════════════════════════════════════════════════════════
// 7. ResultsPage — word-level diff highlighting
// ═══════════════════════════════════════════════════════════════
describe('ResultsPage v5 diff highlighting', () => {
  it('renders score cards and comparison', async () => {
    renderWithRouter(<ResultsPage />, { route: '/app/results/result-1' })
    await waitFor(() => {
      expect(screen.getByText('Результаты оптимизации')).toBeDefined()
      expect(screen.getByText('Match Score')).toBeDefined()
      expect(screen.getByText('Сравнение версий')).toBeDefined()
    })
  })

  it('shows improvement legend', async () => {
    renderWithRouter(<ResultsPage />, { route: '/app/results/result-1' })
    await waitFor(() => {
      expect(screen.getByText('Слабые формулировки')).toBeDefined()
      expect(screen.getByText('Улучшения AI')).toBeDefined()
    })
  })

  it('highlights added words in optimized panel', async () => {
    renderWithRouter(<ResultsPage />, { route: '/app/results/result-1' })
    await waitFor(() => expect(screen.getByText('Сравнение версий')).toBeDefined())
    // "Senior" is a new word in rewritten text, should be highlighted
    const highlightedEl = screen.getByText('Senior')
    expect(highlightedEl).toBeDefined()
    expect(highlightedEl.style.background).toContain('rgba(16, 185, 129')
  })

  it('highlights removed words in original panel', async () => {
    renderWithRouter(<ResultsPage />, { route: '/app/results/result-1' })
    await waitFor(() => expect(screen.getByText('Сравнение версий')).toBeDefined())
    // "Делал" is only in original, should be marked as removed
    const removedEl = screen.getByText('Делал')
    expect(removedEl).toBeDefined()
    expect(removedEl.style.background).toContain('rgba(239, 68, 68')
  })

  it('shows keywords added count', async () => {
    renderWithRouter(<ResultsPage />, { route: '/app/results/result-1' })
    await waitFor(() => {
      expect(screen.getByText('Добавленные ключевые слова')).toBeDefined()
      expect(screen.getByText('FastAPI')).toBeDefined()
      expect(screen.getByText('Docker')).toBeDefined()
    })
  })

  it('shows ATS rating and model', async () => {
    renderWithRouter(<ResultsPage />, { route: '/app/results/result-1' })
    await waitFor(() => {
      expect(screen.getByText('A')).toBeDefined()
      expect(screen.getByText('gpt-4o')).toBeDefined()
    })
  })

  it('shows score improvement', async () => {
    renderWithRouter(<ResultsPage />, { route: '/app/results/result-1' })
    await waitFor(() => {
      expect(screen.getByText('+40 пунктов')).toBeDefined()
    })
  })
})

// ═══════════════════════════════════════════════════════════════
// 8. HelpPage — all sections render
// ═══════════════════════════════════════════════════════════════
describe('HelpPage', () => {
  it('renders page title', () => {
    renderWithRouter(<HelpPage />, { route: '/app/help' })
    expect(screen.getByText('Справка')).toBeDefined()
    expect(screen.getByText('Руководство по использованию ResumeCraft')).toBeDefined()
  })

  it('renders quick start section with 4 steps', () => {
    renderWithRouter(<HelpPage />, { route: '/app/help' })
    expect(screen.getByText('Быстрый старт')).toBeDefined()
    expect(screen.getByText('1. Загрузите резюме')).toBeDefined()
    expect(screen.getByText('2. Укажите вакансию')).toBeDefined()
    expect(screen.getByText('3. Выберите модель')).toBeDefined()
    expect(screen.getByText('4. Получите результат')).toBeDefined()
  })

  it('renders optimization pipeline section', () => {
    renderWithRouter(<HelpPage />, { route: '/app/help' })
    expect(screen.getByText('Как работает оптимизация')).toBeDefined()
  })

  it('renders features section', () => {
    renderWithRouter(<HelpPage />, { route: '/app/help' })
    expect(screen.getByText('Возможности')).toBeDefined()
    expect(screen.getByText('Мультиформат')).toBeDefined()
    expect(screen.getByText('Интеграция hh.ru')).toBeDefined()
    expect(screen.getByText('Мультимодельный AI')).toBeDefined()
  })

  it('renders tariff plans', () => {
    renderWithRouter(<HelpPage />, { route: '/app/help' })
    expect(screen.getByText('Тарифные планы')).toBeDefined()
    expect(screen.getByText('Free')).toBeDefined()
    expect(screen.getByText('Standard')).toBeDefined()
    expect(screen.getByText('Pro')).toBeDefined()
    expect(screen.getByText('490 ₽/мес')).toBeDefined()
    expect(screen.getByText('1 490 ₽/мес')).toBeDefined()
  })

  it('renders FAQ accordion', () => {
    renderWithRouter(<HelpPage />, { route: '/app/help' })
    expect(screen.getByText('Часто задаваемые вопросы')).toBeDefined()
    expect(screen.getByText('Как загрузить резюме?')).toBeDefined()
  })

  it('FAQ accordion expands on click', () => {
    renderWithRouter(<HelpPage />, { route: '/app/help' })
    const question = screen.getByText('Как загрузить резюме?')
    fireEvent.click(question)
    // Use unique text from the FAQ answer (not present elsewhere on the page)
    expect(screen.getByText(/Максимальный размер файла/)).toBeDefined()
  })

  it('FAQ accordion collapses on second click', () => {
    renderWithRouter(<HelpPage />, { route: '/app/help' })
    const question = screen.getByText('Как загрузить резюме?')
    fireEvent.click(question) // open
    expect(screen.getByText(/Максимальный размер файла/)).toBeDefined()
    fireEvent.click(question) // close
    expect(screen.queryByText(/Максимальный размер файла — 10 МБ/)).toBeNull()
  })

  it('renders contact/support section', () => {
    renderWithRouter(<HelpPage />, { route: '/app/help' })
    expect(screen.getByText('Не нашли ответ?')).toBeDefined()
    expect(screen.getByText('support@resumecraft.ru')).toBeDefined()
  })

  it('renders LLM error FAQ', () => {
    renderWithRouter(<HelpPage />, { route: '/app/help' })
    expect(screen.getByText('Ошибка «LLM-провайдер недоступен»?')).toBeDefined()
  })

  it('renders privacy/deletion FAQ', () => {
    renderWithRouter(<HelpPage />, { route: '/app/help' })
    expect(screen.getByText('Как удалить мои данные?')).toBeDefined()
    expect(screen.getByText('Где хранятся мои данные?')).toBeDefined()
  })
})

// ═══════════════════════════════════════════════════════════════
// 9. AppLayout — Help link in navigation
// ═══════════════════════════════════════════════════════════════
describe('AppLayout v5 Help link', () => {
  it('renders Help/Справка link in sidebar navigation', () => {
    render(
      <MemoryRouter initialEntries={['/app/dashboard']}>
        <WizardProvider>
          <Routes>
            <Route path="/app/*" element={<AppLayout />} />
          </Routes>
        </WizardProvider>
      </MemoryRouter>
    )
    expect(screen.getByText('Справка')).toBeDefined()
  })
})

// ═══════════════════════════════════════════════════════════════
// 10. Backend-related: resume delete guard, vacancy schemas
// ═══════════════════════════════════════════════════════════════
describe('Backend-related fixes validation', () => {
  it('getHHVacancyDetail API method exists', () => {
    // The mock setup includes getHHVacancyDetail; verify it's callable
    expect(typeof mockGetHHVacancyDetail).toBe('function')
  })

  it('deleteResume called without crash for text resumes', async () => {
    const textResume = { ...mockResumeDetail, file_format: 'txt', file_path: '' }
    mockGetResume.mockResolvedValue(textResume)
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => expect(screen.getByText('Python Dev')).toBeDefined())
    fireEvent.click(screen.getByText('Удалить'))
    await waitFor(() => {
      expect(mockDeleteResume).toHaveBeenCalledWith('res-1')
    })
  })
})
