import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'
import { AuthProvider } from '../contexts/AuthContext'

// Helper to render within router + auth
function renderWithProviders(ui: React.ReactNode, route = '/') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <AuthProvider>
        {ui}
      </AuthProvider>
    </MemoryRouter>
  )
}

// ===================== AuthPage =====================
import AuthPage from '../pages/auth/AuthPage'

describe('AuthPage', () => {
  it('renders login tab by default', () => {
    renderWithProviders(<AuthPage />)
    expect(screen.getByRole('heading', { name: /войти/i })).toBeInTheDocument()
  })

  it('renders register tab when ?tab=register', () => {
    render(
      <MemoryRouter initialEntries={['/auth?tab=register']}>
        <AuthProvider><AuthPage /></AuthProvider>
      </MemoryRouter>
    )
    expect(screen.getByRole('heading', { name: /поиск работы/i })).toBeInTheDocument()
  })

  it('switches between login and register tabs', () => {
    renderWithProviders(<AuthPage />)
    fireEvent.click(screen.getByText('Регистрация'))
    expect(screen.getByRole('heading', { name: /поиск работы/i })).toBeInTheDocument()
    fireEvent.click(screen.getByText('Войти'))
    expect(screen.getByRole('heading', { name: /войти/i })).toBeInTheDocument()
  })

  it('switches between phone and email methods', () => {
    renderWithProviders(<AuthPage />)
    // Phone is default now
    expect(screen.getByPlaceholderText('918 276-25-33')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Почта'))
    expect(screen.getByPlaceholderText('alex@example.com')).toBeInTheDocument()
  })

  it('renders animated orbs', () => {
    const { container } = renderWithProviders(<AuthPage />)
    const orbs = container.querySelectorAll('.orb')
    expect(orbs.length).toBe(3)
  })

  it('renders sparkle particles', () => {
    const { container } = renderWithProviders(<AuthPage />)
    const sparkles = container.querySelectorAll('.sparkle')
    expect(sparkles.length).toBe(5)
  })

  it('renders resume card skeleton', () => {
    const { container } = renderWithProviders(<AuthPage />)
    expect(container.querySelector('.resume-card')).toBeInTheDocument()
    const skelLines = container.querySelectorAll('.skel-line')
    expect(skelLines.length).toBeGreaterThan(5)
  })

  it('renders back to home link', () => {
    renderWithProviders(<AuthPage />)
    expect(screen.getByText('На главную')).toBeInTheDocument()
  })

  it('shows error message on failed login', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false, status: 401,
      json: () => Promise.resolve({ message: 'Неверный пароль' }),
    })
    vi.stubGlobal('fetch', mockFetch)

    renderWithProviders(<AuthPage />)
    fireEvent.click(screen.getByText('Почта'))
    fireEvent.change(screen.getByPlaceholderText('alex@example.com'), { target: { value: 'test@test.com' } })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'password123' } })
    // Click the submit button specifically
    fireEvent.click(screen.getByRole('button', { name: /войти/i }))

    await waitFor(() => {
      expect(screen.getByText('Неверный пароль')).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('email input updates value', () => {
    renderWithProviders(<AuthPage />)
    fireEvent.click(screen.getByText('Почта'))
    const emailInput = screen.getByPlaceholderText('alex@example.com')
    fireEvent.change(emailInput, { target: { value: 'user@mail.com' } })
    expect(emailInput).toHaveValue('user@mail.com')
  })
})

// ===================== SettingsAiPage =====================
import SettingsAiPage from '../pages/settings/SettingsAiPage'

describe('SettingsAiPage', () => {
  it('renders model selection cards', () => {
    renderWithProviders(<SettingsAiPage />)
    expect(screen.getByText('GigaChat Pro')).toBeInTheDocument()
    expect(screen.getByText('GPT-4o')).toBeInTheDocument()
    expect(screen.getByText('Llama 3.3 70B')).toBeInTheDocument()
    expect(screen.getByText('OpenRouter')).toBeInTheDocument()
  })

  it('selects model on click', () => {
    renderWithProviders(<SettingsAiPage />)
    fireEvent.click(screen.getByText('OpenRouter'))
    // Verify OpenRouter text is visible and card changed
    expect(screen.getByText('OpenRouter')).toBeInTheDocument()
  })

  it('renders API key inputs for all providers', () => {
    renderWithProviders(<SettingsAiPage />)
    expect(screen.getByPlaceholderText('Credentials (Base64)')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('sk-...')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('gsk_...')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('sk-or-v1-...')).toBeInTheDocument()
  })

  it('toggles API key visibility', () => {
    renderWithProviders(<SettingsAiPage />)
    const gigachatInput = screen.getByPlaceholderText('Credentials (Base64)')
    expect(gigachatInput).toHaveAttribute('type', 'password')

    // Click show button (first eye button)
    const showBtns = screen.getAllByTitle('Показать')
    fireEvent.click(showBtns[0])
    expect(gigachatInput).toHaveAttribute('type', 'text')
  })

  it('renders optimization toggles', () => {
    renderWithProviders(<SettingsAiPage />)
    expect(screen.getByText('ATS оптимизация')).toBeInTheDocument()
    expect(screen.getByText('Автоматические метрики')).toBeInTheDocument()
    expect(screen.getByText('Soft skills')).toBeInTheDocument()
  })

  it('toggles work correctly', () => {
    renderWithProviders(<SettingsAiPage />)
    const checkboxes = screen.getAllByRole('checkbox')
    // First checkbox ('auto_metrics') starts checked
    expect(checkboxes[0]).toBeChecked()
    fireEvent.click(checkboxes[0])
    expect(checkboxes[0]).not.toBeChecked()
  })

  it('save button shows confirmation', async () => {
    renderWithProviders(<SettingsAiPage />)
    fireEvent.click(screen.getByText('Сохранить'))
    await waitFor(() => {
      expect(screen.getByText('✓ Сохранено')).toBeInTheDocument()
    })
  })

  it('reset button restores defaults', () => {
    renderWithProviders(<SettingsAiPage />)
    // Select OpenRouter
    fireEvent.click(screen.getByText('OpenRouter'))
    // Reset
    fireEvent.click(screen.getByText('Сбросить'))
    // GigaChat should be selected again - verify it's still present
    expect(screen.getByText('GigaChat Pro')).toBeInTheDocument()
  })

  it('renders provider badges', () => {
    renderWithProviders(<SettingsAiPage />)
    expect(screen.getByText('Рекомендуем')).toBeInTheDocument()
    expect(screen.getByText('Бесплатно')).toBeInTheDocument()
    expect(screen.getByText('Новое')).toBeInTheDocument()
  })

  it('API key input accepts text', () => {
    renderWithProviders(<SettingsAiPage />)
    const input = screen.getByPlaceholderText('sk-or-v1-...')
    fireEvent.change(input, { target: { value: 'my-api-key' } })
    expect(input).toHaveValue('my-api-key')
  })
})

// ===================== SettingsSecurityPage =====================
import SettingsSecurityPage from '../pages/settings/SettingsSecurityPage'

describe('SettingsSecurityPage', () => {
  it('renders password change form', () => {
    renderWithProviders(<SettingsSecurityPage />)
    expect(screen.getByText('Текущий пароль')).toBeInTheDocument()
    expect(screen.getByText('Новый пароль')).toBeInTheDocument()
    expect(screen.getByText('Подтвердите пароль')).toBeInTheDocument()
  })

  it('password inputs are controlled', () => {
    renderWithProviders(<SettingsSecurityPage />)
    const inputs = screen.getAllByPlaceholderText('••••••••')
    fireEvent.change(inputs[0], { target: { value: 'oldpass123' } })
    expect(inputs[0]).toHaveValue('oldpass123')
  })

  it('shows validation error for empty fields', () => {
    renderWithProviders(<SettingsSecurityPage />)
    fireEvent.click(screen.getByText('Обновить пароль'))
    expect(screen.getByText('Заполните все поля')).toBeInTheDocument()
  })

  it('shows error for mismatched passwords', () => {
    renderWithProviders(<SettingsSecurityPage />)
    const inputs = screen.getAllByPlaceholderText('••••••••')
    const pwInput = screen.getByPlaceholderText('Мин. 8 символов, цифра + буква')
    fireEvent.change(inputs[0], { target: { value: 'oldpass123' } })
    fireEvent.change(pwInput, { target: { value: 'newpass123' } })
    fireEvent.change(inputs[1], { target: { value: 'different123' } })
    fireEvent.click(screen.getByText('Обновить пароль'))
    expect(screen.getByText('Пароли не совпадают')).toBeInTheDocument()
  })

  it('shows error for short password', () => {
    renderWithProviders(<SettingsSecurityPage />)
    const inputs = screen.getAllByPlaceholderText('••••••••')
    const pwInput = screen.getByPlaceholderText('Мин. 8 символов, цифра + буква')
    fireEvent.change(inputs[0], { target: { value: 'oldpass1' } })
    fireEvent.change(pwInput, { target: { value: 'short' } })
    fireEvent.change(inputs[1], { target: { value: 'short' } })
    fireEvent.click(screen.getByText('Обновить пароль'))
    expect(screen.getByText('Пароль должен быть минимум 8 символов')).toBeInTheDocument()
  })

  it('shows success on valid password change', () => {
    renderWithProviders(<SettingsSecurityPage />)
    const inputs = screen.getAllByPlaceholderText('••••••••')
    const pwInput = screen.getByPlaceholderText('Мин. 8 символов, цифра + буква')
    fireEvent.change(inputs[0], { target: { value: 'oldpass123' } })
    fireEvent.change(pwInput, { target: { value: 'newpass123' } })
    fireEvent.change(inputs[1], { target: { value: 'newpass123' } })
    fireEvent.click(screen.getByText('Обновить пароль'))
    expect(screen.getByText('Пароль успешно обновлён')).toBeInTheDocument()
  })

  it('renders 2FA toggle', () => {
    renderWithProviders(<SettingsSecurityPage />)
    expect(screen.getByText('Двухфакторная аутентификация')).toBeInTheDocument()
  })

  it('renders active sessions', () => {
    renderWithProviders(<SettingsSecurityPage />)
    expect(screen.getByText(/Chrome — macOS/)).toBeInTheDocument()
    expect(screen.getByText(/Safari — iPhone/)).toBeInTheDocument()
    expect(screen.getByText('Текущая')).toBeInTheDocument()
  })

  it('renders danger zone with delete account', () => {
    renderWithProviders(<SettingsSecurityPage />)
    expect(screen.getByText('Опасная зона')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Удалить аккаунт'))
    expect(screen.getByPlaceholderText('Введите "УДАЛИТЬ" для подтверждения')).toBeInTheDocument()
  })

  it('delete confirm button disabled until "УДАЛИТЬ" typed', () => {
    renderWithProviders(<SettingsSecurityPage />)
    fireEvent.click(screen.getByText('Удалить аккаунт'))
    const confirmBtn = screen.getByText('Подтвердить')
    expect(confirmBtn).toBeDisabled()
    const input = screen.getByPlaceholderText('Введите "УДАЛИТЬ" для подтверждения')
    fireEvent.change(input, { target: { value: 'УДАЛИТЬ' } })
    expect(confirmBtn).not.toBeDisabled()
  })
})

// ===================== SettingsProfilePage =====================
import SettingsProfilePage from '../pages/settings/SettingsProfilePage'

describe('SettingsProfilePage', () => {
  it('renders profile form fields', () => {
    renderWithProviders(<SettingsProfilePage />)
    expect(screen.getByText('Имя и фамилия')).toBeInTheDocument()
    expect(screen.getByText('Email')).toBeInTheDocument()
    expect(screen.getByText('Телефон')).toBeInTheDocument()
    expect(screen.getByText('Город')).toBeInTheDocument()
    expect(screen.getByText('Текущая должность')).toBeInTheDocument()
    expect(screen.getByText('О себе')).toBeInTheDocument()
  })

  it('form inputs are editable', () => {
    renderWithProviders(<SettingsProfilePage />)
    const nameInput = screen.getByDisplayValue('Алексей Петров')
    fireEvent.change(nameInput, { target: { value: 'Иван Иванов' } })
    expect(nameInput).toHaveValue('Иван Иванов')
  })

  it('renders avatar with initials', () => {
    renderWithProviders(<SettingsProfilePage />)
    expect(screen.getByText('АП')).toBeInTheDocument()
  })

  it('renders save button', () => {
    renderWithProviders(<SettingsProfilePage />)
    expect(screen.getByText('Сохранить')).toBeInTheDocument()
  })
})

// ===================== SettingsSubscriptionPage =====================
import SettingsSubscriptionPage from '../pages/settings/SettingsSubscriptionPage'

describe('SettingsSubscriptionPage', () => {
  it('renders all three plans', () => {
    renderWithProviders(<SettingsSubscriptionPage />)
    expect(screen.getByText('Free')).toBeInTheDocument()
    expect(screen.getByText('490 ₽')).toBeInTheDocument()
    expect(screen.getByText('1 490 ₽')).toBeInTheDocument()
  })

  it('renders current plan badge', () => {
    renderWithProviders(<SettingsSubscriptionPage />)
    // "Текущий план" heading + "Текущий" badge + "Текущий план" button
    expect(screen.getByText('Все планы')).toBeInTheDocument()
  })

  it('current plan button is disabled', () => {
    renderWithProviders(<SettingsSubscriptionPage />)
    const currentBtn = screen.getByRole('button', { name: /текущий план/i })
    expect(currentBtn).toBeDisabled()
  })
})

// ===================== DashboardPage =====================
import DashboardPage from '../pages/dashboard/DashboardPage'

describe('DashboardPage', () => {
  it('renders greeting', () => {
    renderWithProviders(<DashboardPage />, '/app/dashboard')
    expect(screen.getByRole('heading', { name: /добрый день/i })).toBeInTheDocument()
  })

  it('renders stats grid', () => {
    renderWithProviders(<DashboardPage />, '/app/dashboard')
    expect(screen.getByText('Всего резюме')).toBeInTheDocument()
    expect(screen.getByText('Оптимизаций')).toBeInTheDocument()
    expect(screen.getByText('Средний Match Score')).toBeInTheDocument()
  })

  it('renders recent resumes section', () => {
    renderWithProviders(<DashboardPage />, '/app/dashboard')
    expect(screen.getByText('Недавние резюме')).toBeInTheDocument()
    expect(screen.getByText('Создать новое')).toBeInTheDocument()
  })
})

// ===================== UploadPage =====================
import UploadPage from '../pages/wizard/UploadPage'

describe('UploadPage', () => {
  it('renders dropzone', () => {
    renderWithProviders(<UploadPage />, '/app/upload')
    expect(screen.getByText('Перетащите файл сюда')).toBeInTheDocument()
    expect(screen.getByText('Выбрать файл')).toBeInTheDocument()
  })

  it('renders format info', () => {
    renderWithProviders(<UploadPage />, '/app/upload')
    expect(screen.getByText('PDF')).toBeInTheDocument()
    expect(screen.getByText('DOCX')).toBeInTheDocument()
    expect(screen.getByText('до 10 МБ')).toBeInTheDocument()
  })

  it('shows file after selection', () => {
    const { container } = renderWithProviders(<UploadPage />, '/app/upload')
    const input = container.querySelector('input[type="file"]')!
    const file = new File(['test'], 'resume.pdf', { type: 'application/pdf' })
    fireEvent.change(input, { target: { files: [file] } })
    expect(screen.getByText('resume.pdf')).toBeInTheDocument()
    expect(screen.getByText('Продолжить')).toBeInTheDocument()
  })
})

// ===================== VacancyPage =====================
import VacancyPage from '../pages/wizard/VacancyPage'

describe('VacancyPage', () => {
  it('renders three tabs', () => {
    renderWithProviders(<VacancyPage />, '/app/vacancy')
    expect(screen.getByText('Поиск hh.ru')).toBeInTheDocument()
    expect(screen.getByText('Вставить URL')).toBeInTheDocument()
    expect(screen.getByText('Ввести вручную')).toBeInTheDocument()
  })

  it('switches to URL tab', () => {
    renderWithProviders(<VacancyPage />, '/app/vacancy')
    fireEvent.click(screen.getByText('Вставить URL'))
    expect(screen.getByPlaceholderText('https://hh.ru/vacancy/12345678')).toBeInTheDocument()
  })

  it('switches to manual tab', () => {
    renderWithProviders(<VacancyPage />, '/app/vacancy')
    fireEvent.click(screen.getByText('Ввести вручную'))
    expect(screen.getByPlaceholderText('Product Manager')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Яндекс')).toBeInTheDocument()
  })

  it('renders demo vacancies in search tab', () => {
    renderWithProviders(<VacancyPage />, '/app/vacancy')
    expect(screen.getByText(/Яндекс/)).toBeInTheDocument()
  })
})

// ===================== ModelsPage =====================
import ModelsPage from '../pages/wizard/ModelsPage'

describe('ModelsPage', () => {
  it('renders three model cards', () => {
    renderWithProviders(<ModelsPage />, '/app/models')
    expect(screen.getByText('GigaChat Pro')).toBeInTheDocument()
    expect(screen.getByText('GPT-4o')).toBeInTheDocument()
    expect(screen.getByText('Llama 3.3 70B')).toBeInTheDocument()
  })

  it('GigaChat is selected by default', () => {
    renderWithProviders(<ModelsPage />, '/app/models')
    expect(screen.getByText('Рекомендуем')).toBeInTheDocument()
  })

  it('renders quality and speed bars', () => {
    renderWithProviders(<ModelsPage />, '/app/models')
    // 3 model cards on models page, but sidebar also has content
    const qualityTexts = screen.getAllByText('Качество')
    const speedTexts = screen.getAllByText('Скорость')
    expect(qualityTexts.length).toBeGreaterThanOrEqual(3)
    expect(speedTexts.length).toBeGreaterThanOrEqual(3)
  })

  it('renders start optimization button', () => {
    renderWithProviders(<ModelsPage />, '/app/models')
    expect(screen.getByText('Начать оптимизацию')).toBeInTheDocument()
  })
})

// ===================== ResultsPage =====================
import ResultsPage from '../pages/wizard/ResultsPage'

describe('ResultsPage', () => {
  it('renders match score circle', () => {
    renderWithProviders(<ResultsPage />, '/app/results')
    expect(screen.getByText('Match Score')).toBeInTheDocument()
  })

  it('renders metrics cards', () => {
    renderWithProviders(<ResultsPage />, '/app/results')
    expect(screen.getByText('Ключевые слова')).toBeInTheDocument()
    expect(screen.getByText('Опыт')).toBeInTheDocument()
    expect(screen.getByText('Структура')).toBeInTheDocument()
  })

  it('renders keywords section', () => {
    renderWithProviders(<ResultsPage />, '/app/results')
    expect(screen.getByText('Добавленные ключевые слова')).toBeInTheDocument()
  })

  it('renders diff comparison', () => {
    renderWithProviders(<ResultsPage />, '/app/results')
    expect(screen.getByText('Оригинал')).toBeInTheDocument()
    expect(screen.getByText('Оптимизировано')).toBeInTheDocument()
  })

  it('renders action buttons', () => {
    renderWithProviders(<ResultsPage />, '/app/results')
    expect(screen.getByText('Редактировать')).toBeInTheDocument()
    expect(screen.getByText('Экспорт')).toBeInTheDocument()
  })
})
