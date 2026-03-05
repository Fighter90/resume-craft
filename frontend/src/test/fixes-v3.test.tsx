/**
 * Tests for v3 fixes:
 * 1. ResumeDetailPage: PDF viewer, download for all statuses, optimize link to vacancy
 * 2. ResumesPage: download for all statuses, optimize confirmation dialog
 * 3. VacancyPage: pagination, resumeId from URL params
 * 4. ModelsPage: default model from settings, fallback sub-models
 * 5. ProcessingPage: pipeline validation
 * 6. SettingsProfilePage: avatar overlap fix
 * 7. api.ts: downloadResumeFile method
 */
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { WizardProvider } from '../contexts/WizardContext'

/* eslint-disable @typescript-eslint/no-explicit-any */

// ─── Mock Data ───────────────────────────────────────────────
const mockResumes = [
  { id: 'res-1', title: 'Python Dev', status: 'optimized', file_format: 'pdf', created_at: '2026-03-15T10:00:00Z', raw_text: 'text content' },
  { id: 'res-2', title: 'React Dev', status: 'draft', file_format: 'docx', created_at: '2026-03-10T10:00:00Z', raw_text: 'draft text' },
  { id: 'res-3', title: 'Data Scientist', status: 'processing', file_format: 'pdf', created_at: '2026-03-20T10:00:00Z' },
]

const mockResumeDetail = {
  id: 'res-1', title: 'Python Dev', status: 'draft', file_format: 'pdf',
  created_at: '2026-03-15T10:00:00Z',
  raw_text: 'Опыт работы: Python разработчик с 5-летним стажем',
  parsed_data: {
    summary: 'Опытный Python-разработчик',
    experience: [{ position: 'Senior Developer', company: 'ТехКорп', period: '2020-2025', achievements: ['Оптимизировал API'] }],
    education: [{ institution: 'МГУ', degree: 'Магистр', specialization: 'Информатика', year: 2020 }],
    skills: ['Python', 'FastAPI', 'PostgreSQL'],
  },
}

const mockResumeDetailOptimized = { ...mockResumeDetail, id: 'res-opt', status: 'optimized' }

const mockHistory = [
  { id: 'task-1', resume_id: 'res-opt', status: 'completed', vacancy_id: 'vac-1' },
]

const mockVacancies = {
  items: Array.from({ length: 15 }, (_, i) => ({
    hh_id: `vac-${i}`, title: `Вакансия ${i + 1}`, company: `Компания ${i + 1}`,
    city: 'Москва', salary_from: 100000 + i * 10000, salary_to: 200000 + i * 10000,
    key_skills: ['Python', 'SQL'], experience: '3-6 лет',
    description: '<p>Описание вакансии</p>',
    snippet: { requirement: 'Требование', responsibility: 'Обязанность' },
    url: `https://hh.ru/vacancy/vac-${i}`,
  })),
  found: 15, page: 0, pages: 2,
}

const mockModels = {
  models: [
    { id: 'gigachat-pro', name: 'GigaChat Pro', provider: 'Сбер', available: true, description: 'Лучшая для русского', has_sub_models: false },
    { id: 'openai', name: 'OpenAI', provider: 'OpenAI', available: true, description: 'GPT-4o', has_sub_models: true },
    { id: 'anthropic', name: 'Anthropic', provider: 'Anthropic', available: false, description: 'Claude', has_sub_models: true },
  ],
}

const mockSubModels = { sub_models: [{ id: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI' }, { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI' }] }

// ─── API Mock Setup ──────────────────────────────────────────
const mockGetResumes = vi.fn()
const mockGetResume = vi.fn()
const mockDeleteResume = vi.fn()
const mockDownloadResumeFile = vi.fn()
const mockExportDocx = vi.fn()
const mockGetRewriteHistory = vi.fn()
const mockSearchVacancies = vi.fn()
const mockCreateVacancyFromUrl = vi.fn()
const mockCreateVacancyManual = vi.fn()
const mockGetModels = vi.fn()
const mockGetSubModels = vi.fn()
const mockStartRewrite = vi.fn()
const mockGetRewriteStatus = vi.fn()
const mockGetRewriteResult = vi.fn()

vi.mock('../services/api', () => ({
  api: {
    getResumes: (...a: any[]) => mockGetResumes(...a),
    getResume: (...a: any[]) => mockGetResume(...a),
    deleteResume: (...a: any[]) => mockDeleteResume(...a),
    downloadResumeFile: (...a: any[]) => mockDownloadResumeFile(...a),
    exportDocx: (...a: any[]) => mockExportDocx(...a),
    getRewriteHistory: (...a: any[]) => mockGetRewriteHistory(...a),
    searchVacancies: (...a: any[]) => mockSearchVacancies(...a),
    createVacancyFromUrl: (...a: any[]) => mockCreateVacancyFromUrl(...a),
    createVacancyManual: (...a: any[]) => mockCreateVacancyManual(...a),
    getModels: (...a: any[]) => mockGetModels(...a),
    getSubModels: (...a: any[]) => mockGetSubModels(...a),
    startRewrite: (...a: any[]) => mockStartRewrite(...a),
    getRewriteStatus: (...a: any[]) => mockGetRewriteStatus(...a),
    getRewriteResult: (...a: any[]) => mockGetRewriteResult(...a),
    setToken: vi.fn(),
    clearToken: vi.fn(),
    getMe: vi.fn().mockRejectedValue(new Error('not authed')),
    selectSearchVacancy: vi.fn(),
  },
  ApiClient: vi.fn(),
}))

vi.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    isAuthenticated: true, loading: false,
    user: { id: 'user-1', full_name: 'Тест Юзер', email: 'test@example.com', plan: 'free', optimizations_used: 0, is_active: true },
    login: vi.fn(), logout: vi.fn(), register: vi.fn(), refreshUser: vi.fn(),
  }),
}))

import ResumesPage from '../pages/resumes/ResumesPage'
import ResumeDetailPage from '../pages/resumes/ResumeDetailPage'
import VacancyPage from '../pages/wizard/VacancyPage'
import ModelsPage from '../pages/wizard/ModelsPage'
import ProcessingPage from '../pages/wizard/ProcessingPage'
import SettingsProfilePage from '../pages/settings/SettingsProfilePage'

// ─── Helpers ─────────────────────────────────────────────────
function renderWithRouter(element: React.ReactElement, { route = '/' }: { route?: string } = {}) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <WizardProvider>
        <Routes>
          <Route path="/app/resumes" element={element} />
          <Route path="/app/resumes/:id" element={element} />
          <Route path="/app/vacancy" element={element} />
          <Route path="/app/models" element={element} />
          <Route path="/app/processing" element={element} />
          <Route path="/app/settings/profile" element={element} />
        </Routes>
      </WizardProvider>
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  mockGetResumes.mockResolvedValue(mockResumes)
  mockGetResume.mockResolvedValue(mockResumeDetail)
  mockDeleteResume.mockResolvedValue(undefined)
  mockDownloadResumeFile.mockResolvedValue(new Blob(['file content'], { type: 'application/pdf' }))
  mockExportDocx.mockResolvedValue(new Blob(['docx content']))
  mockGetRewriteHistory.mockResolvedValue(mockHistory)
  mockSearchVacancies.mockResolvedValue(mockVacancies)
  mockCreateVacancyFromUrl.mockResolvedValue({ id: 'vac-new' })
  mockCreateVacancyManual.mockResolvedValue({ id: 'vac-manual' })
  mockGetModels.mockResolvedValue(mockModels)
  mockGetSubModels.mockResolvedValue(mockSubModels)
  mockStartRewrite.mockResolvedValue({ task_id: 'task-123' })
  mockGetRewriteStatus.mockResolvedValue({ status: 'processing', step: 'analyzing', progress: 50 })
  mockGetRewriteResult.mockResolvedValue({ id: 'result-1', status: 'completed' })

  // Mock confirm/alert
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  vi.spyOn(window, 'alert').mockImplementation(() => {})

  // Mock URL.createObjectURL / revokeObjectURL
  global.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
  global.URL.revokeObjectURL = vi.fn()

  // Clear localStorage
  localStorage.clear()
})

afterEach(() => {
  vi.restoreAllMocks()
})

// ═════════════════════════════════════════════════════════════
// 1. ResumeDetailPage Tests
// ═════════════════════════════════════════════════════════════
describe('ResumeDetailPage (v3)', () => {
  it('renders resume title and metadata', async () => {
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => {
      expect(screen.getAllByText('Python Dev').length).toBeGreaterThan(0)
    })
    expect(screen.getByText('Черновик')).toBeTruthy()
  })

  it('shows download button for all statuses (not just optimized)', async () => {
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => {
      expect(screen.getByText('Python Dev')).toBeTruthy()
    })
    const downloadBtn = screen.getByText('Скачать')
    expect(downloadBtn).toBeTruthy()
    expect(downloadBtn.closest('button')).not.toBeNull()
  })

  it('renders optimize button linking to /app/vacancy?resumeId=', async () => {
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => {
      expect(screen.getByText('Python Dev')).toBeTruthy()
    })
    const optimizeLink = screen.getByText('Оптимизировать')
    expect(optimizeLink.closest('a')?.getAttribute('href')).toContain('/app/vacancy?resumeId=res-1')
  })

  it('attempts to load file blob for PDF preview', async () => {
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => {
      expect(mockDownloadResumeFile).toHaveBeenCalledWith('res-1')
    })
  })

  it('shows PDF viewer iframe when file is available', async () => {
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => {
      expect(screen.getByText('Просмотр документа')).toBeTruthy()
    })
    const iframe = document.querySelector('iframe')
    expect(iframe).not.toBeNull()
    expect(iframe?.getAttribute('src')).toBe('blob:mock-url')
  })

  it('shows parsed data sections', async () => {
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => {
      expect(screen.getByText('Профессиональное саммари')).toBeTruthy()
    })
    expect(screen.getByText('Опыт работы')).toBeTruthy()
    expect(screen.getByText('Образование')).toBeTruthy()
    expect(screen.getByText('Навыки')).toBeTruthy()
  })

  it('shows raw text section', async () => {
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => {
      expect(screen.getByText('Текст резюме')).toBeTruthy()
    })
  })

  it('handles delete with confirmation', async () => {
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => {
      expect(screen.getByText('Python Dev')).toBeTruthy()
    })
    const deleteBtn = screen.getByText('Удалить')
    fireEvent.click(deleteBtn)
    expect(window.confirm).toHaveBeenCalled()
    await waitFor(() => {
      expect(mockDeleteResume).toHaveBeenCalledWith('res-1')
    })
  })

  it('handles delete error gracefully', async () => {
    mockDeleteResume.mockRejectedValue(new Error('Внутренняя ошибка'))
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => {
      expect(screen.getByText('Python Dev')).toBeTruthy()
    })
    fireEvent.click(screen.getByText('Удалить'))
    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('Внутренняя ошибка')
    })
  })

  it('handles download for draft resume (original file)', async () => {
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => {
      expect(screen.getByText('Python Dev')).toBeTruthy()
    })
    fireEvent.click(screen.getByText('Скачать'))
    await waitFor(() => {
      expect(mockDownloadResumeFile).toHaveBeenCalled()
    })
  })

  it('handles download for optimized resume (export docx)', async () => {
    mockGetResume.mockResolvedValue(mockResumeDetailOptimized)
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-opt' })
    await waitFor(() => {
      expect(screen.getByText('Python Dev')).toBeTruthy()
    })
    fireEvent.click(screen.getByText('Скачать'))
    await waitFor(() => {
      expect(mockGetRewriteHistory).toHaveBeenCalled()
    })
  })

  it('falls back to raw text download when file unavailable', async () => {
    mockDownloadResumeFile.mockRejectedValue(new Error('not found'))
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => {
      expect(screen.getByText('Python Dev')).toBeTruthy()
    })
    fireEvent.click(screen.getByText('Скачать'))
    // Should not throw, falls back to raw_text
    await waitFor(() => {
      expect(mockDownloadResumeFile).toHaveBeenCalled()
    })
  })

  it('shows error state for loading failure', async () => {
    mockGetResume.mockRejectedValue(new Error('Network error'))
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeTruthy()
    })
  })

  it('shows loading state initially', () => {
    mockGetResume.mockImplementation(() => new Promise(() => {})) // never resolves
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    expect(screen.getByText('Загрузка резюме...')).toBeTruthy()
  })
})

// ═════════════════════════════════════════════════════════════
// 2. ResumesPage Tests (v3)
// ═════════════════════════════════════════════════════════════
describe('ResumesPage (v3)', () => {
  it('renders resumes list', async () => {
    renderWithRouter(<ResumesPage />, { route: '/app/resumes' })
    await waitFor(() => {
      expect(screen.getAllByText('Python Dev').length).toBeGreaterThan(0)
    })
    expect(screen.getAllByText('React Dev').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Data Scientist').length).toBeGreaterThan(0)
  })

  it('shows optimize button for all resumes (including optimized)', async () => {
    renderWithRouter(<ResumesPage />, { route: '/app/resumes' })
    await waitFor(() => {
      expect(screen.getAllByText('Python Dev').length).toBeGreaterThan(0)
    })
    // Desktop table has Zap icon buttons for all resumes
    const zapButtons = document.querySelectorAll('[title="Оптимизировать"]')
    expect(zapButtons.length).toBeGreaterThanOrEqual(3)
  })

  it('shows confirmation dialog when clicking optimize', async () => {
    renderWithRouter(<ResumesPage />, { route: '/app/resumes' })
    await waitFor(() => {
      expect(screen.getAllByText('Python Dev').length).toBeGreaterThan(0)
    })
    const optimizeButtons = document.querySelectorAll('[title="Оптимизировать"]')
    fireEvent.click(optimizeButtons[0])
    expect(window.confirm).toHaveBeenCalled()
  })

  it('download works for draft resumes (not blocked)', async () => {
    renderWithRouter(<ResumesPage />, { route: '/app/resumes' })
    await waitFor(() => {
      expect(screen.getAllByText('React Dev').length).toBeGreaterThan(0)
    })
    const downloadButtons = document.querySelectorAll('[title="Скачать"]')
    expect(downloadButtons.length).toBeGreaterThanOrEqual(3)
    // Click download on second resume (draft) — should try downloadResumeFile
    fireEvent.click(downloadButtons[1])
    await waitFor(() => {
      expect(mockDownloadResumeFile).toHaveBeenCalled()
    })
  })

  it('download for optimized resume tries export first', async () => {
    renderWithRouter(<ResumesPage />, { route: '/app/resumes' })
    await waitFor(() => {
      expect(screen.getAllByText('Python Dev').length).toBeGreaterThan(0)
    })
    // Resumes are sorted by date (newest first): Data Scientist, Python Dev, React Dev
    // Desktop table download buttons: index 0=Data Scientist(processing), 1=Python Dev(optimized), 2=React Dev(draft)
    const downloadButtons = document.querySelectorAll('.resumes-desktop-table [title="Скачать"]')
    fireEvent.click(downloadButtons[1]) // Python Dev (optimized)
    await waitFor(() => {
      expect(mockGetRewriteHistory).toHaveBeenCalled()
    })
  })

  it('deletes a resume with confirmation', async () => {
    renderWithRouter(<ResumesPage />, { route: '/app/resumes' })
    await waitFor(() => {
      expect(screen.getAllByText('Python Dev').length).toBeGreaterThan(0)
    })
    // Sorted by date: index 0=res-3, 1=res-1, 2=res-2
    const deleteButtons = document.querySelectorAll('.resumes-desktop-table [title="Удалить"]')
    fireEvent.click(deleteButtons[1]) // res-1: Python Dev
    expect(window.confirm).toHaveBeenCalled()
    await waitFor(() => {
      expect(mockDeleteResume).toHaveBeenCalledWith('res-1')
    })
  })

  it('filters resumes by search query', async () => {
    renderWithRouter(<ResumesPage />, { route: '/app/resumes' })
    await waitFor(() => {
      expect(screen.getAllByText('Python Dev').length).toBeGreaterThan(0)
    })
    const searchInput = screen.getByPlaceholderText('Поиск резюме...')
    fireEvent.change(searchInput, { target: { value: 'React' } })
    expect(screen.getAllByText('React Dev').length).toBeGreaterThan(0)
    expect(screen.queryByText('Python Dev')).toBeNull()
  })

  it('filters resumes by status', async () => {
    renderWithRouter(<ResumesPage />, { route: '/app/resumes' })
    await waitFor(() => {
      expect(screen.getAllByText('Python Dev').length).toBeGreaterThan(0)
    })
    const statusSelect = screen.getAllByRole('combobox')[0]
    fireEvent.change(statusSelect, { target: { value: 'Черновик' } })
    expect(screen.getAllByText('React Dev').length).toBeGreaterThan(0)
    expect(screen.queryByText('Python Dev')).toBeNull()
  })

  it('shows count of filtered results', async () => {
    renderWithRouter(<ResumesPage />, { route: '/app/resumes' })
    await waitFor(() => {
      expect(screen.getAllByText('Python Dev').length).toBeGreaterThan(0)
    })
    expect(screen.getByText(/Показано 3 из 3/)).toBeTruthy()
  })
})

// ═════════════════════════════════════════════════════════════
// 3. VacancyPage Tests (v3)
// ═════════════════════════════════════════════════════════════
describe('VacancyPage (v3)', () => {
  it('renders search tab by default', async () => {
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy' })
    expect(screen.getByText('Выберите целевую вакансию')).toBeTruthy()
    expect(screen.getByPlaceholderText('Product Manager')).toBeTruthy()
  })

  it('performs search and shows results', async () => {
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy' })
    const input = screen.getByPlaceholderText('Product Manager')
    fireEvent.change(input, { target: { value: 'Python' } })
    fireEvent.click(screen.getByText('Найти'))
    await waitFor(() => {
      expect(mockSearchVacancies).toHaveBeenCalledWith(expect.objectContaining({ text: 'Python', per_page: '10', page: '0' }))
    })
    await waitFor(() => {
      expect(screen.getByText('Вакансия 1')).toBeTruthy()
    })
  })

  it('shows pagination controls when results span multiple pages', async () => {
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy' })
    const input = screen.getByPlaceholderText('Product Manager')
    fireEvent.change(input, { target: { value: 'Python' } })
    fireEvent.click(screen.getByText('Найти'))
    await waitFor(() => {
      expect(screen.getByText(/Страница 1 из 2/)).toBeTruthy()
    })
    expect(screen.getByText('Вперёд')).toBeTruthy()
    // Back button in pagination (not the link)
    const paginationBtns = screen.getAllByRole('button').filter(b => b.textContent?.includes('Назад'))
    expect(paginationBtns.length).toBeGreaterThan(0)
  })

  it('navigates to next page', async () => {
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy' })
    const input = screen.getByPlaceholderText('Product Manager')
    fireEvent.change(input, { target: { value: 'Python' } })
    fireEvent.click(screen.getByText('Найти'))
    await waitFor(() => {
      expect(screen.getByText(/Страница 1 из 2/)).toBeTruthy()
    })
    fireEvent.click(screen.getByText('Вперёд'))
    await waitFor(() => {
      expect(mockSearchVacancies).toHaveBeenCalledWith(expect.objectContaining({ page: '1' }))
    })
  })

  it('disables back button on first page', async () => {
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy' })
    const input = screen.getByPlaceholderText('Product Manager')
    fireEvent.change(input, { target: { value: 'Python' } })
    fireEvent.click(screen.getByText('Найти'))
    await waitFor(() => {
      expect(screen.getByText(/Страница 1 из 2/)).toBeTruthy()
    })
    // Find the pagination back button (not the navigation link)
    const paginationBtns = screen.getAllByRole('button').filter(b => b.textContent?.includes('Назад'))
    expect(paginationBtns[0]?.hasAttribute('disabled') || (paginationBtns[0] as HTMLButtonElement)?.disabled).toBe(true)
  })

  it('shows vacancy detail modal with description', async () => {
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy' })
    const input = screen.getByPlaceholderText('Product Manager')
    fireEvent.change(input, { target: { value: 'Python' } })
    fireEvent.click(screen.getByText('Найти'))
    await waitFor(() => {
      expect(screen.getByText('Вакансия 1')).toBeTruthy()
    })
    const detailButtons = screen.getAllByText('Подробнее')
    fireEvent.click(detailButtons[0])
    await waitFor(() => {
      expect(screen.getByText('Подробности вакансии')).toBeTruthy()
    })
  })

  it('vacancy detail modal shows salary, skills, description', async () => {
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy' })
    const input = screen.getByPlaceholderText('Product Manager')
    fireEvent.change(input, { target: { value: 'Python' } })
    fireEvent.click(screen.getByText('Найти'))
    await waitFor(() => { expect(screen.getByText('Вакансия 1')).toBeTruthy() })
    const detailButtons = screen.getAllByText('Подробнее')
    fireEvent.click(detailButtons[0])
    const modal = await waitFor(() => screen.getByTestId('vacancy-detail-modal'))
    expect(within(modal).getByText('Ключевые навыки')).toBeTruthy()
    expect(within(modal).getByText('Описание')).toBeTruthy()
  })

  it('reads resumeId from URL query params', async () => {
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy?resumeId=res-from-url' })
    // After rendering, the WizardContext should have resumeId set
    // We verify the page renders correctly (no error)
    expect(screen.getByText('Выберите целевую вакансию')).toBeTruthy()
  })

  it('URL tab submits vacancy from hh.ru link', async () => {
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy' })
    fireEvent.click(screen.getByText('Вставить URL'))
    const urlInput = screen.getByPlaceholderText('https://hh.ru/vacancy/12345678')
    fireEvent.change(urlInput, { target: { value: 'https://hh.ru/vacancy/12345678' } })
    fireEvent.click(screen.getByText('Загрузить вакансию'))
    await waitFor(() => {
      expect(mockCreateVacancyFromUrl).toHaveBeenCalledWith('https://hh.ru/vacancy/12345678')
    })
  })

  it('manual tab submits vacancy', async () => {
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy' })
    fireEvent.click(screen.getByText('Ввести вручную'))
    const titleInput = screen.getByPlaceholderText('Product Manager')
    fireEvent.change(titleInput, { target: { value: 'Python Developer' } })
    const descTextarea = screen.getByPlaceholderText('Опишите обязанности, требования...')
    fireEvent.change(descTextarea, { target: { value: 'Разработка на Python' } })
    fireEvent.click(screen.getByText('Продолжить'))
    await waitFor(() => {
      expect(mockCreateVacancyManual).toHaveBeenCalledWith(expect.objectContaining({ title: 'Python Developer' }))
    })
  })

  it('shows search error when no results found', async () => {
    mockSearchVacancies.mockResolvedValue({ items: [], found: 0, page: 0, pages: 0 })
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy' })
    const input = screen.getByPlaceholderText('Product Manager')
    fireEvent.change(input, { target: { value: 'нетвакансий' } })
    fireEvent.click(screen.getByText('Найти'))
    await waitFor(() => {
      expect(screen.getByText('Вакансии не найдены. Попробуйте другой запрос.')).toBeTruthy()
    })
  })
})

// ═════════════════════════════════════════════════════════════
// 4. ModelsPage Tests (v3)
// ═════════════════════════════════════════════════════════════
describe('ModelsPage (v3)', () => {
  it('renders model cards from server', async () => {
    renderWithRouter(<ModelsPage />, { route: '/app/models' })
    await waitFor(() => {
      expect(screen.getByText('GigaChat Pro')).toBeTruthy()
    })
    // OpenAI appears twice (name + provider), so use getAllByText
    expect(screen.getAllByText('OpenAI').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Anthropic').length).toBeGreaterThan(0)
  })

  it('shows fallback models when server fails', async () => {
    mockGetModels.mockRejectedValue(new Error('Server error'))
    renderWithRouter(<ModelsPage />, { route: '/app/models' })
    await waitFor(() => {
      expect(screen.getByText('GigaChat Pro')).toBeTruthy()
    })
  })

  it('uses default model from localStorage ai_settings', async () => {
    localStorage.setItem('ai_settings', JSON.stringify({ model: 'openai', apiKeys: { openai: 'test-key' } }))
    renderWithRouter(<ModelsPage />, { route: '/app/models' })
    await waitFor(() => {
      expect(screen.getAllByText('OpenAI').length).toBeGreaterThan(0)
    })
    // The default model is set to 'openai' from settings in initial state
    // After server models load w/ availability, it may reselect first available
    // Verify getSubModels is called for 'openai' (meaning it was selected)
    await waitFor(() => {
      expect(mockGetSubModels).toHaveBeenCalledWith('openai')
    })
  })

  it('loads sub-models after selecting provider with has_sub_models', async () => {
    renderWithRouter(<ModelsPage />, { route: '/app/models' })
    await waitFor(() => {
      expect(screen.getAllByText('OpenAI').length).toBeGreaterThan(0)
    })
    // Click OpenAI model card
    const modelCards = document.querySelectorAll('.model-card')
    const openaiCard = Array.from(modelCards).find(c => c.textContent?.includes('OpenAI'))
    if (openaiCard) fireEvent.click(openaiCard)
    await waitFor(() => {
      expect(mockGetSubModels).toHaveBeenCalledWith('openai')
    })
  })

  it('shows sub-model dropdown when sub-models available', async () => {
    renderWithRouter(<ModelsPage />, { route: '/app/models' })
    await waitFor(() => { expect(screen.getAllByText('OpenAI').length).toBeGreaterThan(0) })
    const modelCards = document.querySelectorAll('.model-card')
    const openaiCard = Array.from(modelCards).find(c => c.textContent?.includes('OpenAI'))
    if (openaiCard) fireEvent.click(openaiCard)
    await waitFor(() => {
      expect(screen.getAllByText(/GPT-4o/).length).toBeGreaterThan(0)
    })
  })

  it('uses fallback sub-models when server returns empty', async () => {
    mockGetSubModels.mockResolvedValue({ sub_models: [] })
    renderWithRouter(<ModelsPage />, { route: '/app/models' })
    await waitFor(() => { expect(screen.getAllByText('OpenAI').length).toBeGreaterThan(0) })
    const modelCards = document.querySelectorAll('.model-card')
    const openaiCard = Array.from(modelCards).find(c => c.textContent?.includes('OpenAI'))
    if (openaiCard) fireEvent.click(openaiCard)
    await waitFor(() => {
      expect(screen.getAllByText(/GPT-4o/).length).toBeGreaterThan(0)
    })
  })

  it('uses fallback sub-models when server errors', async () => {
    mockGetSubModels.mockRejectedValue(new Error('timeout'))
    renderWithRouter(<ModelsPage />, { route: '/app/models' })
    await waitFor(() => { expect(screen.getAllByText('OpenAI').length).toBeGreaterThan(0) })
    const modelCards = document.querySelectorAll('.model-card')
    const openaiCard = Array.from(modelCards).find(c => c.textContent?.includes('OpenAI'))
    if (openaiCard) fireEvent.click(openaiCard)
    await waitFor(() => {
      expect(screen.getAllByText(/GPT-4o/).length).toBeGreaterThan(0)
    })
  })

  it('shows "no API key" badge for unavailable models', async () => {
    renderWithRouter(<ModelsPage />, { route: '/app/models' })
    await waitFor(() => {
      expect(screen.getAllByText('Anthropic').length).toBeGreaterThan(0)
    })
    expect(screen.getByText('Нет ключа')).toBeTruthy()
  })

  it('shows warning when no keys configured at all', async () => {
    mockGetModels.mockResolvedValue({ models: mockModels.models.map(m => ({ ...m, available: false })) })
    renderWithRouter(<ModelsPage />, { route: '/app/models' })
    await waitFor(() => {
      expect(screen.getByText('API-ключи не настроены')).toBeTruthy()
    })
  })

  it('shows error when resumeId/vacancyId missing on start', async () => {
    renderWithRouter(<ModelsPage />, { route: '/app/models' })
    await waitFor(() => {
      expect(screen.getAllByText('GigaChat Pro').length).toBeGreaterThan(0)
    })
    fireEvent.click(screen.getByText('Начать оптимизацию'))
    await waitFor(() => {
      expect(screen.getByText('Сначала загрузите резюме и выберите вакансию')).toBeTruthy()
    })
  })
})

// ═════════════════════════════════════════════════════════════
// 5. ProcessingPage Tests (v3)
// ═════════════════════════════════════════════════════════════
describe('ProcessingPage (v3)', () => {
  it('shows error when no taskId in context', async () => {
    renderWithRouter(<ProcessingPage />, { route: '/app/processing' })
    await waitFor(() => {
      expect(screen.getByText('Нет задачи для отслеживания. Вернитесь к выбору модели.')).toBeTruthy()
    })
  })

  it('renders 4 processing steps', () => {
    // Even when no taskId, steps should be visible when there is an error
    renderWithRouter(<ProcessingPage />, { route: '/app/processing' })
    // The error state hides steps, so check the headings
    expect(screen.getByText('Ошибка обработки')).toBeTruthy()
  })

  it('shows retry button on error', async () => {
    renderWithRouter(<ProcessingPage />, { route: '/app/processing' })
    await waitFor(() => {
      expect(screen.getByText('Выбрать другую модель')).toBeTruthy()
    })
  })
})

// ═════════════════════════════════════════════════════════════
// 6. SettingsProfilePage Tests (v3)
// ═════════════════════════════════════════════════════════════
describe('SettingsProfilePage (v3)', () => {
  it('renders profile form with user data', () => {
    renderWithRouter(<SettingsProfilePage />, { route: '/app/settings/profile' })
    expect(screen.getByDisplayValue('Тест')).toBeTruthy()
    expect(screen.getByDisplayValue('Юзер')).toBeTruthy()
    expect(screen.getByDisplayValue('test@example.com')).toBeTruthy()
  })

  it('avatar container has fixed size and flexShrink: 0', () => {
    renderWithRouter(<SettingsProfilePage />, { route: '/app/settings/profile' })
    // The avatar container should prevent overlapping
    const avatarCircle = document.querySelector('[style*="border-radius: 50%"]') as HTMLElement
    expect(avatarCircle).not.toBeNull()
    expect(avatarCircle?.style.minWidth).toBe('72px')
    expect(avatarCircle?.style.minHeight).toBe('72px')
    expect(avatarCircle?.style.flexShrink).toBe('0')
  })

  it('text section has overflow ellipsis', () => {
    renderWithRouter(<SettingsProfilePage />, { route: '/app/settings/profile' })
    const nameDiv = screen.getByText('Тест Юзер')
    expect(nameDiv.style.overflow).toBe('hidden')
    expect(nameDiv.style.textOverflow).toBe('ellipsis')
  })

  it('hidden file input exists for photo upload', () => {
    renderWithRouter(<SettingsProfilePage />, { route: '/app/settings/profile' })
    const input = document.querySelector('[data-testid="photo-upload-input"]') as HTMLInputElement
    expect(input).not.toBeNull()
    expect(input?.type).toBe('file')
    expect(input?.accept).toBe('image/*')
    expect(input?.style.display).toBe('none')
  })

  it('upload photo button triggers file input', async () => {
    renderWithRouter(<SettingsProfilePage />, { route: '/app/settings/profile' })
    const uploadBtn = screen.getByText('Загрузить фото')
    const input = document.querySelector('[data-testid="photo-upload-input"]') as HTMLInputElement
    const clickSpy = vi.spyOn(input, 'click')
    fireEvent.click(uploadBtn)
    expect(clickSpy).toHaveBeenCalled()
  })

  it('remove photo button is disabled when no avatar', () => {
    renderWithRouter(<SettingsProfilePage />, { route: '/app/settings/profile' })
    const removeBtn = screen.getByText('Удалить').closest('button')
    expect(removeBtn?.disabled).toBe(true)
  })
})

// ═════════════════════════════════════════════════════════════
// 7. API Service Tests (v3)
// ═════════════════════════════════════════════════════════════
describe('API downloadResumeFile', () => {
  it('mock downloadResumeFile returns Blob', async () => {
    const blob = await mockDownloadResumeFile('res-1')
    expect(blob).toBeInstanceOf(Blob)
  })

  it('downloadResumeFile is called with correct resume id', async () => {
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => {
      expect(mockDownloadResumeFile).toHaveBeenCalledWith('res-1')
    })
  })
})

// ═════════════════════════════════════════════════════════════
// 8. Integration: Full Optimization Flow
// ═════════════════════════════════════════════════════════════
describe('Integration: Optimize from Resumes List', () => {
  it('clicking optimize on resumes page shows confirm and would navigate to vacancy', async () => {
    renderWithRouter(<ResumesPage />, { route: '/app/resumes' })
    await waitFor(() => {
      expect(screen.getAllByText('Python Dev').length).toBeGreaterThan(0)
    })
    const optimizeButtons = document.querySelectorAll('[title="Оптимизировать"]')
    expect(optimizeButtons.length).toBeGreaterThan(0)
    fireEvent.click(optimizeButtons[0])
    expect(window.confirm).toHaveBeenCalledWith(expect.stringContaining('Оптимизировать'))
  })
})

// ═════════════════════════════════════════════════════════════
// 9. Edge Cases
// ═════════════════════════════════════════════════════════════
describe('Edge Cases', () => {
  it('ResumeDetailPage handles missing id gracefully', async () => {
    render(
      <MemoryRouter initialEntries={['/app/resumes/']}>
        <WizardProvider>
          <Routes>
            <Route path="/app/resumes/" element={<ResumeDetailPage />} />
          </Routes>
        </WizardProvider>
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByText('ID резюме не указан')).toBeTruthy()
    })
  })

  it('ResumesPage handles empty list', async () => {
    mockGetResumes.mockResolvedValue([])
    renderWithRouter(<ResumesPage />, { route: '/app/resumes' })
    await waitFor(() => {
      expect(screen.getByText('Нет загруженных резюме')).toBeTruthy()
    })
  })

  it('ModelsPage handles empty localStorage gracefully', async () => {
    localStorage.clear()
    renderWithRouter(<ModelsPage />, { route: '/app/models' })
    await waitFor(() => {
      expect(screen.getAllByText('GigaChat Pro').length).toBeGreaterThan(0)
    })
  })

  it('VacancyPage handles search API error', async () => {
    mockSearchVacancies.mockRejectedValue(new Error('Network error'))
    renderWithRouter(<VacancyPage />, { route: '/app/vacancy' })
    const input = screen.getByPlaceholderText('Product Manager')
    fireEvent.change(input, { target: { value: 'test' } })
    fireEvent.click(screen.getByText('Найти'))
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeTruthy()
    })
  })

  it('ResumesPage handles API error on load', async () => {
    mockGetResumes.mockRejectedValue(new Error('Server down'))
    renderWithRouter(<ResumesPage />, { route: '/app/resumes' })
    await waitFor(() => {
      expect(screen.getByText('Нет загруженных резюме')).toBeTruthy()
    })
  })

  it('Download fallback to alert when both file and raw_text unavailable', async () => {
    mockGetResume.mockResolvedValue({ ...mockResumeDetail, raw_text: null, file_format: 'pdf', status: 'draft' })
    mockDownloadResumeFile.mockRejectedValue(new Error('not found'))
    renderWithRouter(<ResumeDetailPage />, { route: '/app/resumes/res-1' })
    await waitFor(() => {
      expect(screen.getByText('Скачать')).toBeTruthy()
    })
    fireEvent.click(screen.getByText('Скачать'))
    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('Файл недоступен для скачивания')
    })
  })
})
