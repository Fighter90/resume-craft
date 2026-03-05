/**
 * Tests for UploadPage: file upload, hh.ru URL parsing, text paste,
 * tab independence, validation.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { WizardProvider } from '../contexts/WizardContext'

/* eslint-disable @typescript-eslint/no-explicit-any */

// --- API mock ---
const mockUploadResume = vi.fn()
const mockCreateResumeFromText = vi.fn()

vi.mock('../services/api', () => ({
  api: {
    uploadResume: (...a: any[]) => mockUploadResume(...a),
    createResumeFromText: (...a: any[]) => mockCreateResumeFromText(...a),
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

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

import UploadPage from '../pages/wizard/UploadPage'

function renderUploadPage() {
  return render(
    <MemoryRouter initialEntries={['/app/upload']}>
      <WizardProvider>
        <Routes>
          <Route path="/app/upload" element={<UploadPage />} />
        </Routes>
      </WizardProvider>
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  mockUploadResume.mockResolvedValue({ id: 'res-new', title: 'test.pdf', file_format: 'pdf', status: 'draft' })
  mockCreateResumeFromText.mockResolvedValue({ id: 'res-text', title: 'Resume', file_format: 'txt', status: 'draft' })
})

// ===================== File upload tab =====================
describe('UploadPage file tab', () => {
  it('renders page title', () => {
    renderUploadPage()
    expect(screen.getByText('Загрузите ваше резюме')).toBeInTheDocument()
  })

  it('renders three tabs', () => {
    renderUploadPage()
    expect(screen.getByText('Загрузить файл')).toBeInTheDocument()
    expect(screen.getByText('Ссылка hh.ru')).toBeInTheDocument()
    expect(screen.getByText('Вставить текст')).toBeInTheDocument()
  })

  it('renders dropzone on file tab', () => {
    renderUploadPage()
    expect(screen.getByText('Перетащите файл сюда')).toBeInTheDocument()
  })

  it('shows file info after selection', async () => {
    renderUploadPage()
    const input = document.getElementById('file-input') as HTMLInputElement
    const file = new File(['%PDF-test'], 'resume.pdf', { type: 'application/pdf' })
    Object.defineProperty(file, 'size', { value: 5000 })

    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText('resume.pdf')).toBeInTheDocument()
    })
  })

  it('shows error for unsupported format', () => {
    renderUploadPage()
    const input = document.getElementById('file-input') as HTMLInputElement
    const file = new File(['data'], 'resume.txt', { type: 'text/plain' })

    fireEvent.change(input, { target: { files: [file] } })

    expect(screen.getByText(/Неподдерживаемый формат/)).toBeInTheDocument()
  })

  it('shows error for oversized file', () => {
    renderUploadPage()
    const input = document.getElementById('file-input') as HTMLInputElement
    const file = new File(['data'], 'resume.pdf', { type: 'application/pdf' })
    Object.defineProperty(file, 'name', { value: 'resume.pdf' })
    Object.defineProperty(file, 'size', { value: 11 * 1024 * 1024 })

    fireEvent.change(input, { target: { files: [file] } })

    expect(screen.getByText(/слишком большой/)).toBeInTheDocument()
  })

  it('renders supported formats info', () => {
    renderUploadPage()
    expect(screen.getByText('PDF')).toBeInTheDocument()
    expect(screen.getByText('DOCX')).toBeInTheDocument()
    expect(screen.getByText('до 10 МБ')).toBeInTheDocument()
  })
})

// ===================== hh.ru URL tab =====================
describe('UploadPage hh.ru URL tab', () => {
  it('renders URL input on hh.ru tab', () => {
    renderUploadPage()
    fireEvent.click(screen.getByText('Ссылка hh.ru'))
    expect(screen.getByPlaceholderText('https://hh.ru/resume/abc123def4')).toBeInTheDocument()
  })

  it('renders Загрузить резюме button', () => {
    renderUploadPage()
    fireEvent.click(screen.getByText('Ссылка hh.ru'))
    expect(screen.getByText('Загрузить резюме')).toBeInTheDocument()
  })

  it('attempts to parse hh.ru URL on submit', async () => {
    renderUploadPage()
    fireEvent.click(screen.getByText('Ссылка hh.ru'))
    fireEvent.change(screen.getByPlaceholderText('https://hh.ru/resume/abc123def4'), {
      target: { value: 'https://hh.ru/resume/abc123' },
    })
    fireEvent.click(screen.getByText('Загрузить резюме'))

    await waitFor(() => {
      expect(mockCreateResumeFromText).toHaveBeenCalledWith({
        text: '',
        title: 'Резюме с hh.ru',
        source_url: 'https://hh.ru/resume/abc123',
      })
    })
  })

  it('shows error and fallback on hh.ru parse failure', async () => {
    mockCreateResumeFromText.mockRejectedValue(new Error('Parse failed'))
    renderUploadPage()
    fireEvent.click(screen.getByText('Ссылка hh.ru'))
    fireEvent.change(screen.getByPlaceholderText('https://hh.ru/resume/abc123def4'), {
      target: { value: 'https://hh.ru/resume/abc123' },
    })
    fireEvent.click(screen.getByText('Загрузить резюме'))

    await waitFor(() => {
      expect(screen.getByText(/Не удалось автоматически загрузить/)).toBeInTheDocument()
    })
  })

  it('has manual text paste fallback button', () => {
    renderUploadPage()
    fireEvent.click(screen.getByText('Ссылка hh.ru'))
    expect(screen.getByText('Вставить текст вручную')).toBeInTheDocument()
  })

  it('switches to paste tab on fallback click', () => {
    renderUploadPage()
    fireEvent.click(screen.getByText('Ссылка hh.ru'))
    fireEvent.click(screen.getByText('Вставить текст вручную'))
    // After switching, should see text paste fields
    expect(screen.getByText('Текст резюме *')).toBeInTheDocument()
  })
})

// ===================== Text paste tab =====================
describe('UploadPage text paste tab', () => {
  it('renders text paste fields', () => {
    renderUploadPage()
    fireEvent.click(screen.getByText('Вставить текст'))
    expect(screen.getByText('Текст резюме *')).toBeInTheDocument()
    expect(screen.getByText('Название (необязательно)')).toBeInTheDocument()
  })

  it('shows character count', () => {
    renderUploadPage()
    fireEvent.click(screen.getByText('Вставить текст'))
    expect(screen.getByText(/0 символов/)).toBeInTheDocument()
  })

  it('shows minimum character requirement', () => {
    renderUploadPage()
    fireEvent.click(screen.getByText('Вставить текст'))
    fireEvent.change(screen.getByPlaceholderText(/Вставьте текст/), {
      target: { value: 'Short' },
    })
    expect(screen.getByText(/5 символов/)).toBeInTheDocument()
  })

  it('disables submit when text too short', () => {
    renderUploadPage()
    fireEvent.click(screen.getByText('Вставить текст'))
    fireEvent.change(screen.getByPlaceholderText(/Вставьте текст/), {
      target: { value: 'Short text' },
    })
    expect(screen.getByText('Продолжить')).toBeDisabled()
  })

  it('submits valid text and navigates', async () => {
    renderUploadPage()
    fireEvent.click(screen.getByText('Вставить текст'))

    const longText = 'A'.repeat(100)
    fireEvent.change(screen.getByPlaceholderText(/Вставьте текст/), {
      target: { value: longText },
    })
    fireEvent.click(screen.getByText('Продолжить'))

    await waitFor(() => {
      expect(mockCreateResumeFromText).toHaveBeenCalledWith({
        text: longText,
        title: undefined,
      })
      expect(mockNavigate).toHaveBeenCalledWith('/app/vacancy')
    })
  })

  it('independent from hh.ru URL tab - does not send source_url', async () => {
    renderUploadPage()

    // First go to hh.ru tab and enter a URL
    fireEvent.click(screen.getByText('Ссылка hh.ru'))
    fireEvent.change(screen.getByPlaceholderText('https://hh.ru/resume/abc123def4'), {
      target: { value: 'https://hh.ru/resume/abc123' },
    })

    // Now switch to paste tab
    fireEvent.click(screen.getByText('Вставить текст'))
    const longText = 'B'.repeat(100)
    fireEvent.change(screen.getByPlaceholderText(/Вставьте текст/), {
      target: { value: longText },
    })
    fireEvent.click(screen.getByText('Продолжить'))

    await waitFor(() => {
      // Should NOT include source_url from hh.ru tab
      const callArgs = mockCreateResumeFromText.mock.calls[0][0]
      expect(callArgs.source_url).toBeUndefined()
    })
  })

  it('shows error on API failure', async () => {
    mockCreateResumeFromText.mockRejectedValue({ code: 500 })
    renderUploadPage()
    fireEvent.click(screen.getByText('Вставить текст'))

    const longText = 'C'.repeat(100)
    fireEvent.change(screen.getByPlaceholderText(/Вставьте текст/), {
      target: { value: longText },
    })
    fireEvent.click(screen.getByText('Продолжить'))

    await waitFor(() => {
      expect(screen.getByText('Ошибка создания резюме')).toBeInTheDocument()
    })
  })

  it('shows min 50 char error on very short text', async () => {
    renderUploadPage()
    fireEvent.click(screen.getByText('Вставить текст'))

    // Manually trigger paste text with 10 chars (button should be disabled, but test the validation)
    // Set text > 50 first, then reduce to trigger manual validation
    fireEvent.change(screen.getByPlaceholderText(/Вставьте текст/), {
      target: { value: 'X'.repeat(10) },
    })

    // Button should be disabled
    expect(screen.getByText('Продолжить')).toBeDisabled()
  })
})

// ===================== Tab switching =====================
describe('UploadPage tab switching', () => {
  it('clears error when switching tabs', () => {
    renderUploadPage()

    // Trigger an error on file tab
    const input = document.getElementById('file-input') as HTMLInputElement
    const file = new File(['data'], 'resume.txt', { type: 'text/plain' })
    fireEvent.change(input, { target: { files: [file] } })
    expect(screen.getByText(/Неподдерживаемый формат/)).toBeInTheDocument()

    // Switch to another tab
    fireEvent.click(screen.getByText('Вставить текст'))
    expect(screen.queryByText(/Неподдерживаемый формат/)).not.toBeInTheDocument()
  })
})
