/**
 * Tests for VacancyPage: search, vacancy details modal, per-card select buttons,
 * URL tab, manual tab.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { WizardProvider } from '../contexts/WizardContext'

/* eslint-disable @typescript-eslint/no-explicit-any */

// --- Mock data ---
const mockVacancies = [
  {
    hh_id: '12345',
    title: 'Python Developer',
    company: 'ТехноКорп',
    city: 'Москва',
    salary_from: 200000,
    salary_to: 350000,
    key_skills: ['Python', 'FastAPI', 'Docker'],
    url: 'https://hh.ru/vacancy/12345',
    description: 'Разработка backend-сервисов на Python',
    snippet: {
      requirement: 'Опыт от 3 лет с Python',
      responsibility: 'Разработка REST API',
    },
    experience: '3–6 лет',
  },
  {
    hh_id: '67890',
    title: 'Frontend Developer',
    company: 'ВебСтудия',
    city: 'Санкт-Петербург',
    salary_from: 150000,
    key_skills: ['React', 'TypeScript'],
    url: 'https://hh.ru/vacancy/67890',
  },
]

// --- API mock ---
const mockSearchVacancies = vi.fn()
const mockCreateVacancyFromUrl = vi.fn()
const mockCreateVacancyManual = vi.fn()

vi.mock('../services/api', () => ({
  api: {
    searchVacancies: (...a: any[]) => mockSearchVacancies(...a),
    createVacancyFromUrl: (...a: any[]) => mockCreateVacancyFromUrl(...a),
    createVacancyManual: (...a: any[]) => mockCreateVacancyManual(...a),
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

import VacancyPage from '../pages/wizard/VacancyPage'

function renderVacancyPage() {
  return render(
    <MemoryRouter initialEntries={['/app/vacancy']}>
      <WizardProvider>
        <Routes>
          <Route path="/app/vacancy" element={<VacancyPage />} />
        </Routes>
      </WizardProvider>
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  mockSearchVacancies.mockResolvedValue({ items: mockVacancies })
  mockCreateVacancyFromUrl.mockResolvedValue({ id: 'vac-saved-1' })
  mockCreateVacancyManual.mockResolvedValue({ id: 'vac-manual-1' })
})

// ===================== Search tab =====================
describe('VacancyPage search tab', () => {
  it('renders page title and tabs', () => {
    renderVacancyPage()
    expect(screen.getByText('Выберите целевую вакансию')).toBeInTheDocument()
    expect(screen.getByText('Поиск hh.ru')).toBeInTheDocument()
    expect(screen.getByText('Вставить URL')).toBeInTheDocument()
    expect(screen.getByText('Ввести вручную')).toBeInTheDocument()
  })

  it('renders search fields on default tab', () => {
    renderVacancyPage()
    expect(screen.getByText('Должность')).toBeInTheDocument()
    expect(screen.getByText('Город')).toBeInTheDocument()
    expect(screen.getByText('Найти')).toBeInTheDocument()
  })

  it('searches vacancies and shows results', async () => {
    renderVacancyPage()
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'Python Developer' } })
    fireEvent.click(screen.getByText('Найти'))

    await waitFor(() => {
      expect(screen.getByText('Python Developer')).toBeInTheDocument()
    })
    expect(screen.getByText('Frontend Developer')).toBeInTheDocument()
    expect(mockSearchVacancies).toHaveBeenCalled()
  })

  it('shows vacancy salary', async () => {
    renderVacancyPage()
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'test' } })
    fireEvent.click(screen.getByText('Найти'))

    await waitFor(() => {
      expect(screen.getByText(/200[,. \s]?000/)).toBeInTheDocument()
    })
  })

  it('shows vacancy skills badges', async () => {
    renderVacancyPage()
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'test' } })
    fireEvent.click(screen.getByText('Найти'))

    await waitFor(() => {
      expect(screen.getByText('Python')).toBeInTheDocument()
      expect(screen.getByText('FastAPI')).toBeInTheDocument()
    })
  })

  it('shows error when no vacancies found', async () => {
    mockSearchVacancies.mockResolvedValue({ items: [] })
    renderVacancyPage()
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'xyz' } })
    fireEvent.click(screen.getByText('Найти'))

    await waitFor(() => {
      expect(screen.getByText(/Вакансии не найдены/)).toBeInTheDocument()
    })
  })

  it('shows error on search API failure', async () => {
    mockSearchVacancies.mockRejectedValue(new Error('Network error'))
    renderVacancyPage()
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'test' } })
    fireEvent.click(screen.getByText('Найти'))

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
  })

  it('does not search with empty query', () => {
    renderVacancyPage()
    const findBtn = screen.getByText('Найти')
    expect(findBtn).toBeDisabled()
  })
})

// ===================== Per-card buttons =====================
describe('VacancyPage per-card actions', () => {
  it('shows Подробнее and Выбрать buttons on cards', async () => {
    renderVacancyPage()
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'test' } })
    fireEvent.click(screen.getByText('Найти'))

    await waitFor(() => {
      expect(screen.getAllByText('Подробнее').length).toBeGreaterThanOrEqual(2)
      expect(screen.getAllByText('Выбрать').length).toBeGreaterThanOrEqual(2)
    })
  })

  it('Выбрать button saves vacancy and navigates', async () => {
    renderVacancyPage()
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'test' } })
    fireEvent.click(screen.getByText('Найти'))

    await waitFor(() => screen.getAllByText('Выбрать'))
    fireEvent.click(screen.getAllByText('Выбрать')[0])

    await waitFor(() => {
      expect(mockCreateVacancyFromUrl).toHaveBeenCalled()
      expect(mockNavigate).toHaveBeenCalledWith('/app/models')
    })
  })
})

// ===================== Vacancy details modal =====================
describe('VacancyPage vacancy details modal', () => {
  it('opens modal on Подробнее click', async () => {
    renderVacancyPage()
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'test' } })
    fireEvent.click(screen.getByText('Найти'))

    await waitFor(() => screen.getAllByText('Подробнее'))
    fireEvent.click(screen.getAllByText('Подробнее')[0])

    await waitFor(() => {
      expect(screen.getByText('Подробности вакансии')).toBeInTheDocument()
    })
  })

  it('shows vacancy title and company in modal', async () => {
    renderVacancyPage()
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'test' } })
    fireEvent.click(screen.getByText('Найти'))

    await waitFor(() => screen.getAllByText('Подробнее'))
    fireEvent.click(screen.getAllByText('Подробнее')[0])

    await waitFor(() => {
      expect(screen.getByText('Подробности вакансии')).toBeInTheDocument()
      // Title appears both in card and modal
      expect(screen.getAllByText('Python Developer').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('ТехноКорп').length).toBeGreaterThanOrEqual(1)
    })
  })

  it('shows description in modal', async () => {
    renderVacancyPage()
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'test' } })
    fireEvent.click(screen.getByText('Найти'))

    await waitFor(() => screen.getAllByText('Подробнее'))
    fireEvent.click(screen.getAllByText('Подробнее')[0])

    await waitFor(() => {
      expect(screen.getByText(/backend-сервисов/)).toBeInTheDocument()
    })
  })

  it('shows hh.ru link in modal', async () => {
    renderVacancyPage()
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'test' } })
    fireEvent.click(screen.getByText('Найти'))

    await waitFor(() => screen.getAllByText('Подробнее'))
    fireEvent.click(screen.getAllByText('Подробнее')[0])

    await waitFor(() => {
      expect(screen.getByText('Открыть на hh.ru')).toBeInTheDocument()
    })
  })

  it('shows Выбрать эту вакансию button in modal', async () => {
    renderVacancyPage()
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'test' } })
    fireEvent.click(screen.getByText('Найти'))

    await waitFor(() => screen.getAllByText('Подробнее'))
    fireEvent.click(screen.getAllByText('Подробнее')[0])

    await waitFor(() => {
      expect(screen.getByText('Выбрать эту вакансию')).toBeInTheDocument()
    })
  })

  it('closes modal on X button', async () => {
    renderVacancyPage()
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'test' } })
    fireEvent.click(screen.getByText('Найти'))

    await waitFor(() => screen.getAllByText('Подробнее'))
    fireEvent.click(screen.getAllByText('Подробнее')[0])

    await waitFor(() => screen.getByText('Подробности вакансии'))
    fireEvent.click(screen.getByLabelText('Закрыть'))

    await waitFor(() => {
      expect(screen.queryByText('Подробности вакансии')).not.toBeInTheDocument()
    })
  })

  it('selects vacancy from modal and navigates', async () => {
    renderVacancyPage()
    fireEvent.change(screen.getByPlaceholderText('Product Manager'), { target: { value: 'test' } })
    fireEvent.click(screen.getByText('Найти'))

    await waitFor(() => screen.getAllByText('Подробнее'))
    fireEvent.click(screen.getAllByText('Подробнее')[0])

    await waitFor(() => screen.getByText('Выбрать эту вакансию'))
    fireEvent.click(screen.getByText('Выбрать эту вакансию'))

    await waitFor(() => {
      expect(mockCreateVacancyFromUrl).toHaveBeenCalled()
      expect(mockNavigate).toHaveBeenCalledWith('/app/models')
    })
  })
})

// ===================== URL tab =====================
describe('VacancyPage URL tab', () => {
  it('renders URL input when URL tab clicked', () => {
    renderVacancyPage()
    fireEvent.click(screen.getByText('Вставить URL'))
    expect(screen.getByPlaceholderText('https://hh.ru/vacancy/12345678')).toBeInTheDocument()
  })

  it('submits URL and navigates', async () => {
    renderVacancyPage()
    fireEvent.click(screen.getByText('Вставить URL'))
    fireEvent.change(screen.getByPlaceholderText('https://hh.ru/vacancy/12345678'), {
      target: { value: 'https://hh.ru/vacancy/111' },
    })
    fireEvent.click(screen.getByText('Загрузить вакансию'))

    await waitFor(() => {
      expect(mockCreateVacancyFromUrl).toHaveBeenCalledWith('https://hh.ru/vacancy/111')
      expect(mockNavigate).toHaveBeenCalledWith('/app/models')
    })
  })

  it('shows error on URL submit failure', async () => {
    mockCreateVacancyFromUrl.mockRejectedValue(new Error('Invalid URL'))
    renderVacancyPage()
    fireEvent.click(screen.getByText('Вставить URL'))
    fireEvent.change(screen.getByPlaceholderText('https://hh.ru/vacancy/12345678'), {
      target: { value: 'bad-url' },
    })
    fireEvent.click(screen.getByText('Загрузить вакансию'))

    await waitFor(() => {
      expect(screen.getByText('Invalid URL')).toBeInTheDocument()
    })
  })
})

// ===================== Manual tab =====================
describe('VacancyPage manual tab', () => {
  it('renders manual form when Manual tab clicked', () => {
    renderVacancyPage()
    fireEvent.click(screen.getByText('Ввести вручную'))
    expect(screen.getByPlaceholderText('Product Manager')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Яндекс')).toBeInTheDocument()
  })

  it('submits manual vacancy and navigates', async () => {
    renderVacancyPage()
    fireEvent.click(screen.getByText('Ввести вручную'))
    // After switching tabs, Product Manager placeholder appears for title input
    const titleInput = screen.getByPlaceholderText('Product Manager')
    fireEvent.change(titleInput, { target: { value: 'Test Position' } })
    fireEvent.change(screen.getByPlaceholderText('Опишите обязанности, требования...'), {
      target: { value: 'Test Description' },
    })
    fireEvent.click(screen.getByText('Продолжить'))

    await waitFor(() => {
      expect(mockCreateVacancyManual).toHaveBeenCalled()
      expect(mockNavigate).toHaveBeenCalledWith('/app/models')
    })
  })

  it('disables submit when required fields empty', () => {
    renderVacancyPage()
    fireEvent.click(screen.getByText('Ввести вручную'))
    expect(screen.getByText('Продолжить')).toBeDisabled()
  })
})
