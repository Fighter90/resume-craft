/**
 * Tests for ResumesPage (filters, search, status filter, sort, links)
 * and ResumeDetailPage (resume viewing without LLM optimization).
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { WizardProvider } from '../contexts/WizardContext'

/* eslint-disable @typescript-eslint/no-explicit-any */

// --- Mock data ---
const mockResumes = [
  {
    id: 'res-1',
    title: 'Python Developer Resume',
    status: 'optimized',
    file_format: 'pdf',
    created_at: '2026-03-15T10:00:00Z',
  },
  {
    id: 'res-2',
    title: 'Frontend Developer Resume',
    status: 'draft',
    file_format: 'docx',
    created_at: '2026-03-10T10:00:00Z',
  },
  {
    id: 'res-3',
    title: 'Data Scientist Resume',
    status: 'processing',
    file_format: 'pdf',
    created_at: '2026-03-20T10:00:00Z',
  },
]

const mockResumeDetail = {
  id: 'res-1',
  title: 'Python Developer Resume',
  status: 'draft',
  file_format: 'pdf',
  created_at: '2026-03-15T10:00:00Z',
  raw_text: 'Опыт работы: Python разработчик с 5-летним стажем...',
  parsed_data: {
    summary: 'Опытный Python-разработчик с 5-летним стажем в backend',
    experience: [
      { position: 'Senior Developer', company: 'ТехКорп', period: '2020-2025', achievements: ['Оптимизировал API', 'Снизил нагрузку на 40%'] },
    ],
    education: [
      { institution: 'МГУ', degree: 'Магистр', specialization: 'Информатика', year: 2020 },
    ],
    skills: ['Python', 'FastAPI', 'PostgreSQL', 'Docker'],
  },
}

const mockHistory = [
  { id: 'task-1', resume_id: 'res-1', status: 'completed', vacancy_id: 'vac-1' },
]

// --- API mock ---
const mockGetResumes = vi.fn()
const mockDeleteResume = vi.fn()
const mockExportDocx = vi.fn()
const mockGetResume = vi.fn()
const mockGetRewriteHistory = vi.fn()

vi.mock('../services/api', () => ({
  api: {
    getResumes: (...a: any[]) => mockGetResumes(...a),
    deleteResume: (...a: any[]) => mockDeleteResume(...a),
    exportDocx: (...a: any[]) => mockExportDocx(...a),
    getResume: (...a: any[]) => mockGetResume(...a),
    getRewriteHistory: (...a: any[]) => mockGetRewriteHistory(...a),
    setToken: vi.fn(),
    clearToken: vi.fn(),
    getMe: vi.fn().mockRejectedValue(new Error('not authed')),
  },
  ApiClient: vi.fn(),
}))

vi.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({ isAuthenticated: true, loading: false, user: null, login: vi.fn(), logout: vi.fn(), register: vi.fn(), refreshUser: vi.fn() }),
}))

import ResumesPage from '../pages/resumes/ResumesPage'
import ResumeDetailPage from '../pages/resumes/ResumeDetailPage'

function renderResumesPage() {
  return render(
    <MemoryRouter initialEntries={['/app/resumes']}>
      <WizardProvider>
        <Routes>
          <Route path="/app/resumes" element={<ResumesPage />} />
        </Routes>
      </WizardProvider>
    </MemoryRouter>
  )
}

function renderResumeDetail(id: string) {
  return render(
    <MemoryRouter initialEntries={[`/app/resumes/${id}`]}>
      <WizardProvider>
        <Routes>
          <Route path="/app/resumes/:id" element={<ResumeDetailPage />} />
        </Routes>
      </WizardProvider>
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  mockGetResumes.mockResolvedValue(mockResumes)
  mockDeleteResume.mockResolvedValue(undefined)
  mockExportDocx.mockResolvedValue(new Blob(['docx']))
  mockGetResume.mockResolvedValue(mockResumeDetail)
  mockGetRewriteHistory.mockResolvedValue(mockHistory)
  // Mock confirm/alert
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  vi.spyOn(window, 'alert').mockImplementation(() => {})
})

// ===================== ResumesPage =====================
describe('ResumesPage', () => {
  it('renders page title', async () => {
    renderResumesPage()
    expect(screen.getByText('Мои резюме')).toBeInTheDocument()
  })

  it('loads and displays resumes', async () => {
    renderResumesPage()
    await waitFor(() => {
      expect(screen.getAllByText('Python Developer Resume').length).toBeGreaterThanOrEqual(1)
    })
    expect(screen.getAllByText('Frontend Developer Resume').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Data Scientist Resume').length).toBeGreaterThanOrEqual(1)
  })

  it('shows status badges', async () => {
    renderResumesPage()
    await waitFor(() => {
      expect(screen.getAllByText('Оптимизировано').length).toBeGreaterThanOrEqual(1)
    })
    expect(screen.getAllByText('Черновик').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('В обработке').length).toBeGreaterThanOrEqual(1)
  })

  it('renders search input', async () => {
    renderResumesPage()
    expect(screen.getByPlaceholderText('Поиск резюме...')).toBeInTheDocument()
  })

  it('filters resumes by search query', async () => {
    renderResumesPage()
    await waitFor(() => expect(screen.getAllByText('Python Developer Resume').length).toBeGreaterThanOrEqual(1))
    fireEvent.change(screen.getByPlaceholderText('Поиск резюме...'), { target: { value: 'Python' } })

    await waitFor(() => {
      expect(screen.getAllByText('Python Developer Resume').length).toBeGreaterThanOrEqual(1)
      expect(screen.queryAllByText('Frontend Developer Resume').length).toBe(0)
    })
  })

  it('filters by status dropdown', async () => {
    renderResumesPage()
    await waitFor(() => expect(screen.getAllByText('Python Developer Resume').length).toBeGreaterThanOrEqual(1))

    const statusSelect = screen.getByDisplayValue('Все статусы')
    fireEvent.change(statusSelect, { target: { value: 'Черновик' } })

    await waitFor(() => {
      expect(screen.getAllByText('Frontend Developer Resume').length).toBeGreaterThanOrEqual(1)
      expect(screen.queryAllByText('Python Developer Resume').length).toBe(0)
    })
  })

  it('sorts by name', async () => {
    renderResumesPage()
    await waitFor(() => expect(screen.getAllByText('Python Developer Resume').length).toBeGreaterThanOrEqual(1))

    const sortSelect = screen.getByDisplayValue('По дате (новые)')
    fireEvent.change(sortSelect, { target: { value: 'По названию' } })

    // After sorting by name, order should be: Data, Frontend, Python
    await waitFor(() => {
      expect(screen.getAllByText('Data Scientist Resume').length).toBeGreaterThanOrEqual(1)
    })
  })

  it('shows loading state', () => {
    mockGetResumes.mockReturnValue(new Promise(() => {})) // never resolves
    renderResumesPage()
    expect(screen.getByText('Загрузка...')).toBeInTheDocument()
  })

  it('shows empty state when no resumes', async () => {
    mockGetResumes.mockResolvedValue([])
    renderResumesPage()
    await waitFor(() => {
      expect(screen.getByText('Нет загруженных резюме')).toBeInTheDocument()
    })
  })

  it('shows empty search result', async () => {
    renderResumesPage()
    await waitFor(() => expect(screen.getAllByText('Python Developer Resume').length).toBeGreaterThanOrEqual(1))
    fireEvent.change(screen.getByPlaceholderText('Поиск резюме...'), { target: { value: 'zzzzz' } })
    expect(screen.getByText('Ничего не найдено')).toBeInTheDocument()
  })

  it('deletes resume on click', async () => {
    renderResumesPage()
    await waitFor(() => expect(screen.getAllByText('Python Developer Resume').length).toBeGreaterThanOrEqual(1))

    const deleteButtons = screen.getAllByTitle('Удалить')
    fireEvent.click(deleteButtons[0])

    // P2-2: Modal-based delete — confirm in the modal
    await screen.findByText('Удалить резюме?') // wait for modal
    const modalButtons = screen.getAllByRole('button').filter(
      b => b.textContent === 'Удалить' && b.className.includes('btn') && !b.getAttribute('title'),
    )
    fireEvent.click(modalButtons[0])

    await waitFor(() => {
      // After sort by date (newest first): res-3, res-1, res-2
      expect(mockDeleteResume).toHaveBeenCalledWith('res-3')
    })
  })

  it('download works for non-optimized resumes (no alert)', async () => {
    renderResumesPage()
    await waitFor(() => expect(screen.getAllByText('Frontend Developer Resume').length).toBeGreaterThanOrEqual(1))

    // After sort by date (newest): res-3(processing), res-1(optimized), res-2(draft)
    // Desktop table buttons: [0]=res-3, [1]=res-1, [2]=res-2
    const downloadButtons = screen.getAllByTitle('Скачать')
    fireEvent.click(downloadButtons[2]) // res-2 is draft

    // v3: download no longer blocked for non-optimized — no alert shown
    await waitFor(() => {
      expect(window.alert).not.toHaveBeenCalledWith(expect.stringContaining('оптимизированных'))
    })
  })

  it('renders count of resumes', async () => {
    renderResumesPage()
    await waitFor(() => {
      expect(screen.getByText(/Показано 3 из 3/)).toBeInTheDocument()
    })
  })

  it('Eye button opens resume viewer modal', async () => {
    renderResumesPage()
    await waitFor(() => expect(screen.getAllByText('Python Developer Resume').length).toBeGreaterThanOrEqual(1))

    // V19: Eye button is now a <button> that opens viewer modal (not <a> link)
    const viewButtons = screen.getAllByTitle('Просмотр')
    expect(viewButtons[0].tagName).toBe('BUTTON')
    fireEvent.click(viewButtons[0])
  })

  it('renders Загрузить резюме button', () => {
    renderResumesPage()
    expect(screen.getByText('Загрузить резюме')).toBeInTheDocument()
  })
})

// ===================== ResumeDetailPage =====================
describe('ResumeDetailPage', () => {
  it('loads and displays resume title', async () => {
    renderResumeDetail('res-1')
    await waitFor(() => {
      expect(screen.getByText('Python Developer Resume')).toBeInTheDocument()
    })
  })

  it('shows resume status badge', async () => {
    renderResumeDetail('res-1')
    await waitFor(() => {
      expect(screen.getByText('Черновик')).toBeInTheDocument()
    })
  })

  it('shows parsed summary', async () => {
    renderResumeDetail('res-1')
    await waitFor(() => {
      expect(screen.getByText(/Python-разработчик/)).toBeInTheDocument()
    })
  })

  it('shows experience section', async () => {
    renderResumeDetail('res-1')
    await waitFor(() => {
      expect(screen.getByText('Опыт работы')).toBeInTheDocument()
      expect(screen.getByText(/Senior Developer/)).toBeInTheDocument()
      expect(screen.getByText(/ТехКорп/)).toBeInTheDocument()
    })
  })

  it('shows experience achievements', async () => {
    renderResumeDetail('res-1')
    await waitFor(() => {
      expect(screen.getByText('Оптимизировал API')).toBeInTheDocument()
      expect(screen.getByText('Снизил нагрузку на 40%')).toBeInTheDocument()
    })
  })

  it('shows education section', async () => {
    renderResumeDetail('res-1')
    await waitFor(() => {
      expect(screen.getByText('Образование')).toBeInTheDocument()
      expect(screen.getByText('МГУ')).toBeInTheDocument()
    })
  })

  it('shows skills', async () => {
    renderResumeDetail('res-1')
    await waitFor(() => {
      expect(screen.getByText('Навыки')).toBeInTheDocument()
      expect(screen.getByText('Python')).toBeInTheDocument()
      expect(screen.getByText('FastAPI')).toBeInTheDocument()
    })
  })

  it('shows Оптимизировать button', async () => {
    renderResumeDetail('res-1')
    await waitFor(() => {
      expect(screen.getByText('Оптимизировать')).toBeInTheDocument()
    })
  })

  it('shows Удалить button', async () => {
    renderResumeDetail('res-1')
    await waitFor(() => {
      expect(screen.getByText('Удалить')).toBeInTheDocument()
    })
  })

  it('shows error when resume not found', async () => {
    mockGetResume.mockRejectedValue(new Error('Not Found'))
    renderResumeDetail('bad-id')
    await waitFor(() => {
      expect(screen.getByText('Not Found')).toBeInTheDocument()
    })
  })

  it('shows raw text when parsed_data is empty', async () => {
    mockGetResume.mockResolvedValue({
      ...mockResumeDetail,
      parsed_data: null,
      raw_text: 'Просто текст резюме без парсинга',
    })
    renderResumeDetail('res-1')
    await waitFor(() => {
      expect(screen.getByText('Текст резюме')).toBeInTheDocument()
      expect(screen.getByText('Просто текст резюме без парсинга')).toBeInTheDocument()
    })
  })

  it('shows placeholder when no content available', async () => {
    mockGetResume.mockResolvedValue({
      ...mockResumeDetail,
      parsed_data: null,
      raw_text: null,
    })
    renderResumeDetail('res-1')
    await waitFor(() => {
      expect(screen.getByText(/Текст резюме ещё не извлечён/)).toBeInTheDocument()
    })
  })

  it('shows loading state', () => {
    mockGetResume.mockReturnValue(new Promise(() => {}))
    renderResumeDetail('res-1')
    expect(screen.getByText('Загрузка резюме...')).toBeInTheDocument()
  })

  it('shows date', async () => {
    renderResumeDetail('res-1')
    await waitFor(() => {
      expect(screen.getByText(/2026/)).toBeInTheDocument()
    })
  })

  it('shows file format', async () => {
    renderResumeDetail('res-1')
    await waitFor(() => {
      expect(screen.getByText('PDF')).toBeInTheDocument()
    })
  })
})
