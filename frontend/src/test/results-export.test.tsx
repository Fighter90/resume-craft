/**
 * Tests for ResultsPage (URL param loading, vacancy modal)
 * and ExportPage (URL param download).
 *
 * Uses vi.mock to mock the API service.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { WizardProvider } from '../contexts/WizardContext'

/* eslint-disable @typescript-eslint/no-explicit-any */

// --- Mock data ---
const mockResult = {
  id: 'aaa-bbb-ccc',
  resume_id: 'res-1',
  vacancy_id: 'vac-1',
  status: 'completed',
  match_score_before: 45,
  match_score_after: 87,
  ats_rating: 'A+',
  model_name: 'GigaChat Pro',
  processing_time_ms: 12000,
  original_text: 'Оригинальный текст резюме кандидата',
  rewritten_text: 'Оптимизированный текст резюме кандидата',
  rewritten_data: null,
  keywords_added: ['Python', 'FastAPI', 'Docker'],
  tokens_used: 1500,
  created_at: '2026-03-01T12:00:00Z',
}

const mockVacancy = {
  id: 'vac-1',
  title: 'Python Developer',
  company: 'ТехноКорп',
  description: 'Разработка backend-сервисов',
  city: 'Москва',
  salary_from: 200000,
  salary_to: 350000,
  experience: '3–6 лет',
  key_skills: ['Python', 'FastAPI', 'PostgreSQL'],
  requirements: { Опыт: 'от 3 лет', Образование: 'Высшее' },
  source_url: 'https://hh.ru/vacancy/12345',
}

// --- API mock ---
const mockGetRewriteResult = vi.fn()
const mockGetVacancy = vi.fn()
const mockExportDocx = vi.fn()
const mockGetRewriteHistory = vi.fn()

vi.mock('../services/api', () => ({
  api: {
    getRewriteResult: (...a: any[]) => mockGetRewriteResult(...a),
    getVacancy: (...a: any[]) => mockGetVacancy(...a),
    exportDocx: (...a: any[]) => mockExportDocx(...a),
    getRewriteHistory: (...a: any[]) => mockGetRewriteHistory(...a),
    setToken: vi.fn(),
    clearToken: vi.fn(),
    getMe: vi.fn().mockRejectedValue(new Error('not authed')),
  },
  ApiClient: vi.fn(),
}))

// --- Auth context mock (minimal) ---
vi.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({ isAuthenticated: true, loading: false, user: null, login: vi.fn(), logout: vi.fn(), register: vi.fn() }),
}))

// --- Helpers ---
function renderWithRoute(element: React.ReactNode, path: string, route: string) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <WizardProvider>
        <Routes>
          <Route path={path} element={element} />
        </Routes>
      </WizardProvider>
    </MemoryRouter>
  )
}

// --- Imports ---
import ResultsPage from '../pages/wizard/ResultsPage'
import ExportPage from '../pages/wizard/ExportPage'
import HistoryPage from '../pages/history/HistoryPage'

beforeEach(() => {
  vi.clearAllMocks()
  mockGetRewriteResult.mockResolvedValue(mockResult)
  mockGetVacancy.mockResolvedValue(mockVacancy)
  mockExportDocx.mockResolvedValue(new Blob(['docx'], { type: 'application/octet-stream' }))
  mockGetRewriteHistory.mockResolvedValue([
    { ...mockResult, id: 'hist-1' },
    { ...mockResult, id: 'hist-2', status: 'failed', error_message: 'LLM error' },
  ])
})

// ===================== ResultsPage: URL param loading =====================
describe('ResultsPage with URL param', () => {
  it('fetches result by URL id and renders page header', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => {
      expect(screen.getByText('Результаты оптимизации')).toBeInTheDocument()
    })
    expect(mockGetRewriteResult).toHaveBeenCalledWith('aaa-bbb-ccc')
  })

  it('renders Match Score circle', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => {
      expect(screen.getByText('Match Score')).toBeInTheDocument()
    })
  })

  it('renders model name', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => {
      expect(screen.getByText('GigaChat Pro')).toBeInTheDocument()
    })
  })

  it('renders all 4 metric components', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => expect(screen.getByText('Ключевые слова')).toBeInTheDocument())
    expect(screen.getByText('Опыт')).toBeInTheDocument()
    expect(screen.getByText('Структура')).toBeInTheDocument()
    expect(screen.getByText('Читаемость')).toBeInTheDocument()
  })

  it('renders ATS rating', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => {
      expect(screen.getByText('A+')).toBeInTheDocument()
    })
  })

  it('renders keywords', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => expect(screen.getByText('Python')).toBeInTheDocument())
    expect(screen.getByText('FastAPI')).toBeInTheDocument()
    expect(screen.getByText('Docker')).toBeInTheDocument()
  })

  it('renders diff comparison', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => expect(screen.getByText('Оригинал')).toBeInTheDocument())
    expect(screen.getByText('Оптимизировано')).toBeInTheDocument()
    // computeWordDiff splits text into per-word <span> elements,
    // so getByText can't find the full phrase. Check textContent instead.
    const diffPanels = document.querySelectorAll('.diff-content')
    expect(diffPanels[0]?.textContent).toContain('Оригинальный')
    expect(diffPanels[1]?.textContent).toContain('Оптимизированный')
  })

  it('renders action buttons', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => {
      expect(screen.getAllByText('Редактировать').length).toBeGreaterThanOrEqual(1)
    })
    expect(screen.getAllByText('Экспорт').length).toBeGreaterThanOrEqual(1)
  })

  it('shows error on API failure', async () => {
    mockGetRewriteResult.mockRejectedValue(new Error('Not Found'))
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/bad-id')
    await waitFor(() => {
      expect(screen.getByText('Not Found')).toBeInTheDocument()
    })
  })

  it('renders processing time', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => {
      expect(screen.getByText('Время обработки')).toBeInTheDocument()
    })
  })
})

// ===================== Vacancy modal =====================
describe('ResultsPage vacancy modal', () => {
  it('renders vacancy button', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => {
      expect(screen.getByText('Вакансия')).toBeInTheDocument()
    })
  })

  it('opens modal and shows vacancy title', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => screen.getByText('Вакансия'))
    fireEvent.click(screen.getByText('Вакансия'))
    await waitFor(() => {
      expect(screen.getByText('Подробности вакансии')).toBeInTheDocument()
    })
    expect(screen.getByText('Python Developer')).toBeInTheDocument()
  })

  it('shows company name', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => screen.getByText('Вакансия'))
    fireEvent.click(screen.getByText('Вакансия'))
    await waitFor(() => {
      expect(screen.getByText('ТехноКорп')).toBeInTheDocument()
    })
  })

  it('shows city', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => screen.getByText('Вакансия'))
    fireEvent.click(screen.getByText('Вакансия'))
    await waitFor(() => {
      expect(screen.getByText('Москва')).toBeInTheDocument()
    })
  })

  it('shows salary range', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => screen.getByText('Вакансия'))
    fireEvent.click(screen.getByText('Вакансия'))
    await waitFor(() => {
      expect(screen.getByText(/200\s?000/)).toBeInTheDocument()
    })
  })

  it('shows experience', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => screen.getByText('Вакансия'))
    fireEvent.click(screen.getByText('Вакансия'))
    await waitFor(() => {
      expect(screen.getByText('3–6 лет')).toBeInTheDocument()
    })
  })

  it('shows key skills', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => screen.getByText('Вакансия'))
    fireEvent.click(screen.getByText('Вакансия'))
    await waitFor(() => {
      expect(screen.getByText('PostgreSQL')).toBeInTheDocument()
    })
  })

  it('shows requirements', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => screen.getByText('Вакансия'))
    fireEvent.click(screen.getByText('Вакансия'))
    await waitFor(() => {
      expect(screen.getByText(/от 3 лет/)).toBeInTheDocument()
    })
  })

  it('shows hh.ru link', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => screen.getByText('Вакансия'))
    fireEvent.click(screen.getByText('Вакансия'))
    await waitFor(() => {
      expect(screen.getByText('Открыть на hh.ru')).toBeInTheDocument()
    })
  })

  it('closes modal on X button', async () => {
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => screen.getByText('Вакансия'))
    fireEvent.click(screen.getByText('Вакансия'))
    await waitFor(() => screen.getByText('Подробности вакансии'))
    fireEvent.click(screen.getByLabelText('Закрыть'))
    await waitFor(() => {
      expect(screen.queryByText('Подробности вакансии')).not.toBeInTheDocument()
    })
  })

  it('shows error when vacancy API fails', async () => {
    mockGetVacancy.mockRejectedValue(new Error('fail'))
    renderWithRoute(<ResultsPage />, '/app/results/:id', '/app/results/aaa-bbb-ccc')
    await waitFor(() => screen.getByText('Вакансия'))
    fireEvent.click(screen.getByText('Вакансия'))
    await waitFor(() => {
      expect(screen.getByText('Не удалось загрузить данные вакансии')).toBeInTheDocument()
    })
  })
})

// ===================== ExportPage with URL param =====================
describe('ExportPage with URL param', () => {
  it('fetches result and renders format selection', async () => {
    renderWithRoute(<ExportPage />, '/app/export/:id', '/app/export/aaa-bbb-ccc')
    await waitFor(() => {
      expect(screen.getByText('DOCX')).toBeInTheDocument()
    })
    expect(mockGetRewriteResult).toHaveBeenCalledWith('aaa-bbb-ccc')
  })

  it('renders template selection', async () => {
    renderWithRoute(<ExportPage />, '/app/export/:id', '/app/export/aaa-bbb-ccc')
    await waitFor(() => {
      expect(screen.getByText('Минималистичный')).toBeInTheDocument()
    })
    expect(screen.getAllByText('Профессиональный').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Креативный')).toBeInTheDocument()
  })

  it('renders download button', async () => {
    renderWithRoute(<ExportPage />, '/app/export/:id', '/app/export/aaa-bbb-ccc')
    await waitFor(() => {
      expect(screen.getByText(/Скачать DOCX/)).toBeInTheDocument()
    })
  })

  it('renders ready to download section with scores', async () => {
    renderWithRoute(<ExportPage />, '/app/export/:id', '/app/export/aaa-bbb-ccc')
    await waitFor(() => {
      expect(screen.getByText('Готово к скачиванию')).toBeInTheDocument()
    })
    expect(screen.getByText('Match 87%')).toBeInTheDocument()
    expect(screen.getByText('ATS A+')).toBeInTheDocument()
  })
})

// ===================== HistoryPage with mocked API =====================
describe('HistoryPage with API data', () => {
  it('renders completed items with Open button', async () => {
    renderWithRoute(<HistoryPage />, '/app/history', '/app/history')
    await waitFor(() => {
      expect(screen.getAllByText('Открыть').length).toBeGreaterThanOrEqual(1)
    })
  })

  it('renders failed item error text', async () => {
    renderWithRoute(<HistoryPage />, '/app/history', '/app/history')
    await waitFor(() => {
      expect(screen.getByText(/LLM error/)).toBeInTheDocument()
    })
  })

  it('renders model name for each item', async () => {
    renderWithRoute(<HistoryPage />, '/app/history', '/app/history')
    await waitFor(() => {
      expect(screen.getAllByText(/GigaChat Pro/).length).toBeGreaterThanOrEqual(1)
    })
  })

  it('renders dates', async () => {
    renderWithRoute(<HistoryPage />, '/app/history', '/app/history')
    await waitFor(() => {
      expect(screen.getAllByText(/2026/).length).toBeGreaterThanOrEqual(1)
    })
  })

  it('shows empty state when no history', async () => {
    mockGetRewriteHistory.mockResolvedValue([])
    renderWithRoute(<HistoryPage />, '/app/history', '/app/history')
    await waitFor(() => {
      expect(screen.getByText('Нет истории оптимизаций')).toBeInTheDocument()
    })
  })
})
