/**
 * Comprehensive tests for ExportPage — V19 changes.
 *
 * Covers:
 * - Unit: FORMATS array doesn't contain hh.ru
 * - Unit: Only 3 format cards rendered (DOCX, PDF, TXT)
 * - Functional: Selecting TXT hides template section
 * - Functional: Download button updates per format
 * - Functional: "Ready to download" section shows correct filename
 * - Integration: URL param fetches result from API
 * - Acceptance: Complete export flow for each format
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { WizardProvider } from '../contexts/WizardContext'

/* eslint-disable @typescript-eslint/no-explicit-any */

// --- Mock data ---
const mockResult = {
  id: 'export-test-id',
  resume_id: 'res-1',
  vacancy_id: 'vac-1',
  status: 'completed',
  match_score_before: 0.45,
  match_score_after: 0.87,
  ats_rating: 'A+',
  model_name: 'GigaChat Pro',
  processing_time_ms: 12000,
  original_text: 'Original resume text',
  rewritten_text: 'Optimized resume text',
  rewritten_data: null,
  keywords_added: ['Python', 'FastAPI'],
  tokens_used: 1500,
  created_at: '2026-03-01T12:00:00Z',
}

// --- API mock ---
const mockGetRewriteResult = vi.fn()
const mockExportDocx = vi.fn()
const mockExportPdf = vi.fn()
const mockExportTxt = vi.fn()

vi.mock('../services/api', () => ({
  api: {
    getRewriteResult: (...a: any[]) => mockGetRewriteResult(...a),
    exportDocx: (...a: any[]) => mockExportDocx(...a),
    exportPdf: (...a: any[]) => mockExportPdf(...a),
    exportTxt: (...a: any[]) => mockExportTxt(...a),
    setToken: vi.fn(),
    clearToken: vi.fn(),
    getMe: vi.fn().mockRejectedValue(new Error('not authed')),
  },
  ApiClient: vi.fn(),
}))

vi.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    isAuthenticated: true, loading: false, user: null,
    login: vi.fn(), logout: vi.fn(), register: vi.fn(),
  }),
}))

import ExportPage from '../pages/wizard/ExportPage'

function renderExportPage(id = 'export-test-id') {
  return render(
    <MemoryRouter initialEntries={[`/app/export/${id}`]}>
      <WizardProvider>
        <Routes>
          <Route path="/app/export/:id" element={<ExportPage />} />
        </Routes>
      </WizardProvider>
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  mockGetRewriteResult.mockResolvedValue(mockResult)
  mockExportDocx.mockResolvedValue(new Blob(['docx-content'], { type: 'application/octet-stream' }))
  mockExportPdf.mockResolvedValue(new Blob(['pdf-content'], { type: 'application/pdf' }))
  mockExportTxt.mockResolvedValue(new Blob(['txt-content'], { type: 'text/plain' }))
  // Mock createObjectURL/revokeObjectURL
  URL.createObjectURL = vi.fn().mockReturnValue('blob:test')
  URL.revokeObjectURL = vi.fn()
})


// ===================== Unit Tests: Format Cards =====================
describe('ExportPage — Unit: Format cards', () => {
  it('renders exactly 3 format cards (DOCX, PDF, TXT)', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('DOCX')).toBeInTheDocument())
    expect(screen.getByText('PDF')).toBeInTheDocument()
    expect(screen.getByText('TXT')).toBeInTheDocument()
  })

  it('does NOT render hh.ru format card', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('DOCX')).toBeInTheDocument())
    expect(screen.queryByText('hh.ru')).not.toBeInTheDocument()
  })

  it('does NOT show "Обновить резюме на hh.ru напрямую" description', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('DOCX')).toBeInTheDocument())
    expect(screen.queryByText(/hh\.ru напрямую/)).not.toBeInTheDocument()
  })

  it('does NOT show "Скачать HH" button text anywhere', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('DOCX')).toBeInTheDocument())
    expect(screen.queryByText(/Скачать HH/)).not.toBeInTheDocument()
  })

  it('DOCX is selected by default', async () => {
    renderExportPage()
    await waitFor(() => {
      expect(screen.getByText(/Скачать DOCX/)).toBeInTheDocument()
    })
  })

  it('shows TXT description', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('TXT')).toBeInTheDocument())
    expect(screen.getByText('Простой текст — универсальный формат')).toBeInTheDocument()
  })

  it('shows PDF description', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('PDF')).toBeInTheDocument())
    expect(screen.getByText('Универсальный формат для печати')).toBeInTheDocument()
  })

  it('shows DOCX description', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('DOCX')).toBeInTheDocument())
    expect(screen.getByText('Microsoft Word — рекомендуемый формат')).toBeInTheDocument()
  })
})


// ===================== Functional Tests: Format Selection =====================
describe('ExportPage — Functional: Format selection', () => {
  it('clicking TXT card changes button to "Скачать TXT"', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('TXT')).toBeInTheDocument())
    fireEvent.click(screen.getByText('TXT'))
    expect(screen.getByText(/Скачать TXT/)).toBeInTheDocument()
  })

  it('clicking PDF card changes button to "Скачать PDF"', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('PDF')).toBeInTheDocument())
    fireEvent.click(screen.getByText('PDF'))
    expect(screen.getByText(/Скачать PDF/)).toBeInTheDocument()
  })

  it('clicking DOCX card changes button to "Скачать DOCX"', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('DOCX')).toBeInTheDocument())
    // First switch to TXT, then back to DOCX
    fireEvent.click(screen.getByText('TXT'))
    expect(screen.getByText(/Скачать TXT/)).toBeInTheDocument()
    fireEvent.click(screen.getByText('DOCX'))
    expect(screen.getByText(/Скачать DOCX/)).toBeInTheDocument()
  })
})


// ===================== Functional Tests: Template Section =====================
describe('ExportPage — Functional: Template visibility', () => {
  it('shows template section for DOCX', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('DOCX')).toBeInTheDocument())
    expect(screen.getByText('Шаблон оформления')).toBeInTheDocument()
    expect(screen.getByText('Минималистичный')).toBeInTheDocument()
    expect(screen.getByText('Креативный')).toBeInTheDocument()
  })

  it('shows template section for PDF', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('PDF')).toBeInTheDocument())
    fireEvent.click(screen.getByText('PDF'))
    expect(screen.getByText('Шаблон оформления')).toBeInTheDocument()
  })

  it('hides template section for TXT', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('TXT')).toBeInTheDocument())
    fireEvent.click(screen.getByText('TXT'))
    expect(screen.queryByText('Шаблон оформления')).not.toBeInTheDocument()
    expect(screen.getByText('Шаблоны оформления недоступны для формата TXT')).toBeInTheDocument()
  })

  it('restores template section when switching from TXT to DOCX', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('TXT')).toBeInTheDocument())
    fireEvent.click(screen.getByText('TXT'))
    expect(screen.queryByText('Шаблон оформления')).not.toBeInTheDocument()

    fireEvent.click(screen.getByText('DOCX'))
    expect(screen.getByText('Шаблон оформления')).toBeInTheDocument()
  })
})


// ===================== Functional Tests: Ready to Download =====================
describe('ExportPage — Functional: Ready to download section', () => {
  it('shows "Готово к скачиванию" section', async () => {
    renderExportPage()
    await waitFor(() => {
      expect(screen.getByText('Готово к скачиванию')).toBeInTheDocument()
    })
  })

  it('shows correct filename for DOCX', async () => {
    renderExportPage()
    await waitFor(() => {
      expect(screen.getByText('resume_optimized.docx')).toBeInTheDocument()
    })
  })

  it('shows correct filename for TXT', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('TXT')).toBeInTheDocument())
    fireEvent.click(screen.getByText('TXT'))
    expect(screen.getByText('resume_optimized.txt')).toBeInTheDocument()
  })

  it('shows correct filename for PDF', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('PDF')).toBeInTheDocument())
    fireEvent.click(screen.getByText('PDF'))
    expect(screen.getByText('resume_optimized.pdf')).toBeInTheDocument()
  })

  it('shows Match Score', async () => {
    renderExportPage()
    await waitFor(() => {
      expect(screen.getByText('Match 87%')).toBeInTheDocument()
    })
  })

  it('shows ATS rating', async () => {
    renderExportPage()
    await waitFor(() => {
      expect(screen.getByText('ATS A+')).toBeInTheDocument()
    })
  })

  it('shows template name for DOCX (Professional default)', async () => {
    renderExportPage()
    await waitFor(() => {
      expect(screen.getAllByText('Профессиональный').length).toBeGreaterThanOrEqual(1)
    })
  })

  it('shows "—" for template when TXT selected', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('TXT')).toBeInTheDocument())
    fireEvent.click(screen.getByText('TXT'))
    // Template field shows '—' for TXT
    expect(screen.getByText('—')).toBeInTheDocument()
  })
})


// ===================== Integration Tests: API Loading =====================
describe('ExportPage — Integration: API', () => {
  it('fetches result by URL param on mount', async () => {
    renderExportPage('my-export-id')
    await waitFor(() => {
      expect(mockGetRewriteResult).toHaveBeenCalledWith('my-export-id')
    })
  })

  it('shows loading spinner while fetching', () => {
    mockGetRewriteResult.mockReturnValue(new Promise(() => {}))
    renderExportPage()
    expect(screen.getByText('Загрузка данных...')).toBeInTheDocument()
  })

  it('shows error when API fails', async () => {
    mockGetRewriteResult.mockRejectedValue(new Error('Network Error'))
    renderExportPage()
    await waitFor(() => {
      expect(screen.getByText('Не удалось загрузить данные для экспорта')).toBeInTheDocument()
    })
  })
})


// ===================== Integration Tests: Download =====================
describe('ExportPage — Integration: Download', () => {
  it('calls exportDocx when DOCX download clicked', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText(/Скачать DOCX/)).toBeInTheDocument())
    fireEvent.click(screen.getByText(/Скачать DOCX/))
    await waitFor(() => {
      expect(mockExportDocx).toHaveBeenCalledWith('export-test-id')
    })
  })

  it('calls exportPdf when PDF download clicked', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('PDF')).toBeInTheDocument())
    fireEvent.click(screen.getByText('PDF'))
    fireEvent.click(screen.getByText(/Скачать PDF/))
    await waitFor(() => {
      expect(mockExportPdf).toHaveBeenCalledWith('export-test-id')
    })
  })

  it('calls exportTxt when TXT download clicked', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('TXT')).toBeInTheDocument())
    fireEvent.click(screen.getByText('TXT'))
    fireEvent.click(screen.getByText(/Скачать TXT/))
    await waitFor(() => {
      expect(mockExportTxt).toHaveBeenCalledWith('export-test-id')
    })
  })

  it('does NOT call any hh-related export', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('DOCX')).toBeInTheDocument())
    // No hh.ru card means no way to trigger hh export
    expect(screen.queryByText('hh.ru')).not.toBeInTheDocument()
  })

  it('shows download error on API failure', async () => {
    mockExportDocx.mockRejectedValue(new Error('Export failed'))
    renderExportPage()
    await waitFor(() => expect(screen.getByText(/Скачать DOCX/)).toBeInTheDocument())
    fireEvent.click(screen.getByText(/Скачать DOCX/))
    await waitFor(() => {
      expect(screen.getByText('Export failed')).toBeInTheDocument()
    })
  })
})


// ===================== Acceptance Tests: Full Export Flow =====================
describe('ExportPage — Acceptance: Complete flow', () => {
  it('complete DOCX export flow: load → select → download', async () => {
    renderExportPage()
    // 1. Page loads with result
    await waitFor(() => expect(screen.getByText('Экспорт резюме')).toBeInTheDocument())
    // 2. DOCX selected by default
    expect(screen.getByText(/Скачать DOCX/)).toBeInTheDocument()
    // 3. Match score shown
    expect(screen.getByText('Match 87%')).toBeInTheDocument()
    // 4. Click download
    fireEvent.click(screen.getByText(/Скачать DOCX/))
    await waitFor(() => expect(mockExportDocx).toHaveBeenCalled())
  })

  it('complete TXT export flow: load → select TXT → templates hidden → download', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('TXT')).toBeInTheDocument())
    // 1. Select TXT
    fireEvent.click(screen.getByText('TXT'))
    // 2. Templates hidden
    expect(screen.queryByText('Шаблон оформления')).not.toBeInTheDocument()
    expect(screen.getByText('Шаблоны оформления недоступны для формата TXT')).toBeInTheDocument()
    // 3. Filename updated
    expect(screen.getByText('resume_optimized.txt')).toBeInTheDocument()
    // 4. Download
    fireEvent.click(screen.getByText(/Скачать TXT/))
    await waitFor(() => expect(mockExportTxt).toHaveBeenCalled())
  })

  it('complete PDF export flow: load → select PDF → download', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('PDF')).toBeInTheDocument())
    fireEvent.click(screen.getByText('PDF'))
    fireEvent.click(screen.getByText(/Скачать PDF/))
    await waitFor(() => expect(mockExportPdf).toHaveBeenCalled())
  })

  it('format switching: DOCX → TXT → PDF → DOCX', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('DOCX')).toBeInTheDocument())

    // DOCX → TXT
    fireEvent.click(screen.getByText('TXT'))
    expect(screen.getByText(/Скачать TXT/)).toBeInTheDocument()
    expect(screen.queryByText('Шаблон оформления')).not.toBeInTheDocument()

    // TXT → PDF
    fireEvent.click(screen.getByText('PDF'))
    expect(screen.getByText(/Скачать PDF/)).toBeInTheDocument()
    expect(screen.getByText('Шаблон оформления')).toBeInTheDocument()

    // PDF → DOCX
    fireEvent.click(screen.getByText('DOCX'))
    expect(screen.getByText(/Скачать DOCX/)).toBeInTheDocument()
    expect(screen.getByText('Шаблон оформления')).toBeInTheDocument()
  })

  it('no hh.ru anywhere in the export page', async () => {
    renderExportPage()
    await waitFor(() => expect(screen.getByText('DOCX')).toBeInTheDocument())

    // Check there's no hh.ru text anywhere
    const fullText = document.body.textContent || ''
    expect(fullText).not.toContain('hh.ru')
    expect(fullText).not.toContain('Скачать HH')
    expect(fullText).not.toContain('Обновить резюме на hh.ru')
  })
})
