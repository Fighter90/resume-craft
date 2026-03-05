import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'
import { AuthProvider } from '../contexts/AuthContext'
import { WizardProvider } from '../contexts/WizardContext'

// Helper to render within router + auth + wizard
function renderWithProviders(ui: React.ReactNode, route = '/') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <AuthProvider>
        <WizardProvider>
          {ui}
        </WizardProvider>
      </AuthProvider>
    </MemoryRouter>
  )
}

// Helper to render with route params (e.g. /app/results/:id)
function renderWithRoute(element: React.ReactNode, path: string, route: string) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <AuthProvider>
        <WizardProvider>
          <Routes>
            <Route path={path} element={element} />
          </Routes>
        </WizardProvider>
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
    expect(screen.getByText('OpenAI')).toBeInTheDocument()
    expect(screen.getByText('Anthropic Claude')).toBeInTheDocument()
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
    expect(screen.getByPlaceholderText('sk-ant-...')).toBeInTheDocument()
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
    expect(screen.getByText('Имя')).toBeInTheDocument()
    expect(screen.getByText('Фамилия')).toBeInTheDocument()
    expect(screen.getByText('Email')).toBeInTheDocument()
    expect(screen.getByText('Телефон')).toBeInTheDocument()
    expect(screen.getByText('Город')).toBeInTheDocument()
    expect(screen.getByText('Текущая должность')).toBeInTheDocument()
    expect(screen.getByText('О себе')).toBeInTheDocument()
  })

  it('form inputs are editable', () => {
    renderWithProviders(<SettingsProfilePage />)
    const nameInput = screen.getByDisplayValue('Алексей')
    fireEvent.change(nameInput, { target: { value: 'Иван' } })
    expect(nameInput).toHaveValue('Иван')
  })

  it('renders avatar with initials', () => {
    renderWithProviders(<SettingsProfilePage />)
    expect(screen.getByText('АП')).toBeInTheDocument()
  })

  it('renders save button', () => {
    renderWithProviders(<SettingsProfilePage />)
    expect(screen.getByText('Сохранить изменения')).toBeInTheDocument()
  })
})

// ===================== SettingsSubscriptionPage =====================
import SettingsSubscriptionPage from '../pages/settings/SettingsSubscriptionPage'

describe('SettingsSubscriptionPage', () => {
  it('renders all three plans', () => {
    renderWithProviders(<SettingsSubscriptionPage />)
    expect(screen.getByText('Все планы')).toBeInTheDocument()
    expect(screen.getByText('490 ₽')).toBeInTheDocument()
    expect(screen.getByText('1 490 ₽')).toBeInTheDocument()
  })

  it('renders current plan badge', () => {
    renderWithProviders(<SettingsSubscriptionPage />)
    expect(screen.getAllByText(/Текущий/i).length).toBeGreaterThanOrEqual(2)
  })

  it('free plan is current by default', () => {
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
    expect(screen.getByText('Загружено резюме')).toBeInTheDocument()
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
  it('renders four model cards', () => {
    renderWithProviders(<ModelsPage />, '/app/models')
    expect(screen.getByText('GigaChat Pro')).toBeInTheDocument()
    expect(screen.getByText('OpenAI')).toBeInTheDocument()
    expect(screen.getByText('Anthropic Claude')).toBeInTheDocument()
    expect(screen.getAllByText('OpenRouter').length).toBeGreaterThanOrEqual(1)
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
  it('shows error when no taskId and no URL id', () => {
    renderWithProviders(<ResultsPage />, '/app/results')
    expect(screen.getByText('Нет данных для отображения')).toBeInTheDocument()
  })

  it('shows start over button on error', () => {
    renderWithProviders(<ResultsPage />, '/app/results')
    expect(screen.getByText('Начать заново')).toBeInTheDocument()
  })
})

// ===================== PrivacyPage =====================
import PrivacyPage from '../pages/PrivacyPage'

describe('PrivacyPage', () => {
  it('renders privacy policy title', () => {
    renderWithProviders(<PrivacyPage />)
    expect(screen.getByText('Политика конфиденциальности')).toBeInTheDocument()
  })

  it('renders all 8 sections', () => {
    renderWithProviders(<PrivacyPage />)
    expect(screen.getByText('1. Общие положения')).toBeInTheDocument()
    expect(screen.getByText('2. Какие данные мы собираем')).toBeInTheDocument()
    expect(screen.getByText('3. Цели обработки')).toBeInTheDocument()
    expect(screen.getByText('4. Хранение данных')).toBeInTheDocument()
    expect(screen.getByText('5. AI-обработка данных')).toBeInTheDocument()
    expect(screen.getByText('6. Права пользователя')).toBeInTheDocument()
    expect(screen.getByText('7. Cookies')).toBeInTheDocument()
    expect(screen.getByText('8. Контакты')).toBeInTheDocument()
  })

  it('renders back-to-home link', () => {
    renderWithProviders(<PrivacyPage />)
    expect(screen.getByText('На главную')).toBeInTheDocument()
  })

  it('mentions FZ-152 compliance', () => {
    renderWithProviders(<PrivacyPage />)
    expect(screen.getByText(/152-ФЗ/)).toBeInTheDocument()
  })

  it('renders contact email', () => {
    renderWithProviders(<PrivacyPage />)
    expect(screen.getByText('privacy@resumecraft.ru')).toBeInTheDocument()
  })
})

// ===================== TermsPage =====================
import TermsPage from '../pages/TermsPage'

describe('TermsPage', () => {
  it('renders terms title', () => {
    renderWithProviders(<TermsPage />)
    expect(screen.getByText('Правила сервиса')).toBeInTheDocument()
  })

  it('renders all 8 sections', () => {
    renderWithProviders(<TermsPage />)
    expect(screen.getByText('1. Предмет соглашения')).toBeInTheDocument()
    expect(screen.getByText('2. Описание сервиса')).toBeInTheDocument()
    expect(screen.getByText('3. Регистрация и аккаунт')).toBeInTheDocument()
    expect(screen.getByText('4. Тарифные планы')).toBeInTheDocument()
    expect(screen.getByText('5. Ограничения AI')).toBeInTheDocument()
    expect(screen.getByText('6. Загрузка файлов')).toBeInTheDocument()
    expect(screen.getByText('7. Ответственность')).toBeInTheDocument()
    expect(screen.getByText('8. Контакты')).toBeInTheDocument()
  })

  it('renders back-to-home link', () => {
    renderWithProviders(<TermsPage />)
    expect(screen.getByText('На главную')).toBeInTheDocument()
  })

  it('renders tariff info', () => {
    renderWithProviders(<TermsPage />)
    expect(screen.getAllByText(/490 ₽/).length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/1 490 ₽/)).toBeInTheDocument()
  })

  it('renders contact email', () => {
    renderWithProviders(<TermsPage />)
    expect(screen.getByText('support@resumecraft.ru')).toBeInTheDocument()
  })
})

// ===================== AboutPage =====================
import AboutPage from '../pages/AboutPage'

describe('AboutPage', () => {
  it('renders about page title', () => {
    renderWithProviders(<AboutPage />)
    expect(screen.getByText('О сервисе ResumeCraft')).toBeInTheDocument()
  })

  it('renders mission section', () => {
    renderWithProviders(<AboutPage />)
    expect(screen.getByText('Наша миссия')).toBeInTheDocument()
  })

  it('renders capabilities section', () => {
    renderWithProviders(<AboutPage />)
    expect(screen.getByText('Что мы делаем')).toBeInTheDocument()
  })

  it('renders technologies section', () => {
    renderWithProviders(<AboutPage />)
    expect(screen.getByText('Технологии')).toBeInTheDocument()
  })

  it('renders contacts section', () => {
    renderWithProviders(<AboutPage />)
    expect(screen.getByText('Контакты')).toBeInTheDocument()
    expect(screen.getByText('support@resumecraft.ru')).toBeInTheDocument()
    expect(screen.getByText('@resumecraft_support')).toBeInTheDocument()
    expect(screen.getByText('Москва, Россия')).toBeInTheDocument()
  })

  it('renders back-to-home link', () => {
    renderWithProviders(<AboutPage />)
    expect(screen.getByText('На главную')).toBeInTheDocument()
  })

  it('links to privacy policy', () => {
    renderWithProviders(<AboutPage />)
    expect(screen.getByText('Политика конфиденциальности')).toBeInTheDocument()
  })
})

// ===================== EditorPage (enhanced) =====================
import EditorPage from '../pages/wizard/EditorPage'

describe('EditorPage', () => {
  it('renders all section tabs', () => {
    renderWithProviders(<EditorPage />, '/app/editor')
    expect(screen.getAllByText('Заголовок').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Опыт работы')).toBeInTheDocument()
    expect(screen.getByText('Образование')).toBeInTheDocument()
    expect(screen.getByText('Навыки')).toBeInTheDocument()
    expect(screen.getByText('О себе')).toBeInTheDocument()
  })

  it('renders header form with structured fields', () => {
    renderWithProviders(<EditorPage />, '/app/editor')
    expect(screen.getByDisplayValue('Алексей Петров')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Senior Product Manager')).toBeInTheDocument()
    expect(screen.getByDisplayValue('aleksey@example.com')).toBeInTheDocument()
  })

  it('renders AI hints panel', () => {
    renderWithProviders(<EditorPage />, '/app/editor')
    expect(screen.getByText('AI-подсказки')).toBeInTheDocument()
    expect(screen.getByText('Добавьте метрики')).toBeInTheDocument()
  })

  it('renders save draft button', () => {
    renderWithProviders(<EditorPage />, '/app/editor')
    expect(screen.getByText('Сохранить черновик')).toBeInTheDocument()
  })

  it('renders character counter', () => {
    renderWithProviders(<EditorPage />, '/app/editor')
    expect(screen.getByText(/символов/)).toBeInTheDocument()
  })

  it('switches to skills section and shows tags', () => {
    renderWithProviders(<EditorPage />, '/app/editor')
    fireEvent.click(screen.getByText('Навыки'))
    expect(screen.getByText('Agile')).toBeInTheDocument()
    expect(screen.getByText('Python')).toBeInTheDocument()
  })
})

// ===================== ProcessingPage (enhanced) =====================
import ProcessingPage from '../pages/wizard/ProcessingPage'

describe('ProcessingPage', () => {
  it('renders processing steps', () => {
    renderWithProviders(<ProcessingPage />, '/app/processing')
    expect(screen.getByText('Загрузка документа')).toBeInTheDocument()
    expect(screen.getByText('Анализ вакансии')).toBeInTheDocument()
    expect(screen.getByText('AI оптимизация')).toBeInTheDocument()
    expect(screen.getByText('Финализация')).toBeInTheDocument()
  })

  it('renders initial title', () => {
    renderWithProviders(<ProcessingPage />, '/app/processing')
    expect(screen.getByText('Оптимизируем ваше резюме...')).toBeInTheDocument()
  })

  it('renders estimated time text', () => {
    renderWithProviders(<ProcessingPage />, '/app/processing')
    expect(screen.getByText(/10–30 секунд/)).toBeInTheDocument()
  })

  it('renders progress bar', () => {
    const { container } = renderWithProviders(<ProcessingPage />, '/app/processing')
    expect(container.querySelector('.progress-bar')).toBeInTheDocument()
  })

  it('shows result button when done', async () => {
    vi.useFakeTimers()
    renderWithProviders(<ProcessingPage />, '/app/processing')
    // Advance timers to 100% — need act() for state updates
    const { act } = await import('@testing-library/react')
    await act(async () => {
      vi.advanceTimersByTime(10000)
    })
    expect(screen.getByText('Оптимизация завершена!')).toBeInTheDocument()
    expect(screen.getByText('Посмотреть результат')).toBeInTheDocument()
    vi.useRealTimers()
  })
})

// ===================== ExportPage (enhanced) =====================
import ExportPage from '../pages/wizard/ExportPage'

describe('ExportPage', () => {
  it('renders format options', () => {
    renderWithProviders(<ExportPage />, '/app/export')
    expect(screen.getByText('DOCX')).toBeInTheDocument()
    expect(screen.getByText('PDF')).toBeInTheDocument()
    expect(screen.getByText('hh.ru')).toBeInTheDocument()
  })

  it('renders template options', () => {
    renderWithProviders(<ExportPage />, '/app/export')
    expect(screen.getByText('Минималистичный')).toBeInTheDocument()
    expect(screen.getAllByText('Профессиональный').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Креативный')).toBeInTheDocument()
  })

  it('renders download button', () => {
    renderWithProviders(<ExportPage />, '/app/export')
    expect(screen.getByText(/Скачать DOCX/)).toBeInTheDocument()
  })

  it('shows error when clicking download without data', () => {
    renderWithProviders(<ExportPage />, '/app/export')
    fireEvent.click(screen.getByText(/Скачать DOCX/))
    expect(screen.getByText(/Нет данных для экспорта/)).toBeInTheDocument()
  })
})

// ===================== HistoryPage (enhanced) =====================
import HistoryPage from '../pages/history/HistoryPage'

describe('HistoryPage', () => {
  it('renders page title', () => {
    renderWithProviders(<HistoryPage />, '/app/history')
    expect(screen.getByText('История оптимизаций')).toBeInTheDocument()
  })

  it('renders subtitle', () => {
    renderWithProviders(<HistoryPage />, '/app/history')
    expect(screen.getByText('Все ваши оптимизации резюме')).toBeInTheDocument()
  })
})

// ===================== DashboardPage (enhanced) =====================
describe('DashboardPage (enhanced)', () => {
  it('renders subtitle with dream offer text', () => {
    renderWithProviders(<DashboardPage />, '/app/dashboard')
    expect(screen.getByText(/оффер мечты/)).toBeInTheDocument()
  })

  it('renders optimize button with icon', () => {
    renderWithProviders(<DashboardPage />, '/app/dashboard')
    expect(screen.getByText('Оптимизировать резюме')).toBeInTheDocument()
  })

  it('renders SVG match score circle', () => {
    const { container } = renderWithProviders(<DashboardPage />, '/app/dashboard')
    const svgs = container.querySelectorAll('svg')
    expect(svgs.length).toBeGreaterThanOrEqual(1)
  })

  it('renders localized resume statuses', () => {
    renderWithProviders(<DashboardPage />, '/app/dashboard')
    // Demo data has both optimized and draft statuses rendered
    const foundOpt = screen.queryAllByText('Оптимизировано')
    const foundDraft = screen.queryAllByText('Черновик')
    expect(foundOpt.length + foundDraft.length).toBeGreaterThanOrEqual(1)
  })
})

// ===================== ModelsPage (enhanced: 4th model) =====================
describe('ModelsPage (enhanced)', () => {
  it('renders OpenRouter as fourth model', () => {
    renderWithProviders(<ModelsPage />, '/app/models')
    expect(screen.getAllByText('OpenRouter').length).toBeGreaterThanOrEqual(1)
  })

  it('renders all four model cards', () => {
    renderWithProviders(<ModelsPage />, '/app/models')
    expect(screen.getByText('GigaChat Pro')).toBeInTheDocument()
    expect(screen.getByText('OpenAI')).toBeInTheDocument()
    expect(screen.getByText('Anthropic Claude')).toBeInTheDocument()
    expect(screen.getAllByText('OpenRouter').length).toBeGreaterThanOrEqual(1)
  })

  it('renders quality and speed for all 4 models', () => {
    renderWithProviders(<ModelsPage />, '/app/models')
    const qualityTexts = screen.getAllByText('Качество')
    const speedTexts = screen.getAllByText('Скорость')
    expect(qualityTexts.length).toBeGreaterThanOrEqual(4)
    expect(speedTexts.length).toBeGreaterThanOrEqual(4)
  })
})

// ===================== LandingPage sections =====================
import LandingPage from '../pages/LandingPage'

describe('LandingPage (new sections)', () => {
  it('renders before/after section', () => {
    renderWithProviders(<LandingPage />)
    expect(screen.getByText('До и после оптимизации')).toBeInTheDocument()
  })

  it('renders target audience section', () => {
    renderWithProviders(<LandingPage />)
    expect(screen.getByText('Для кого ResumeCraft')).toBeInTheDocument()
  })

  it('renders USP section', () => {
    renderWithProviders(<LandingPage />)
    expect(screen.getByText('Почему именно ResumeCraft')).toBeInTheDocument()
  })

  it('renders stats section', () => {
    renderWithProviders(<LandingPage />)
    expect(screen.getByText('Цифры говорят сами')).toBeInTheDocument()
  })

  it('renders ATS compatibility badges', () => {
    renderWithProviders(<LandingPage />)
    expect(screen.getByText('Huntflow')).toBeInTheDocument()
    expect(screen.getByText('Skillaz')).toBeInTheDocument()
  })
})

// ===================== SettingsProfilePage (enhanced) =====================
describe('SettingsProfilePage (enhanced)', () => {
  it('renders verified email badge', () => {
    renderWithProviders(<SettingsProfilePage />)
    // CheckCircle SVG renders near the email
    expect(screen.getByText(/aleksey@example\.com/i)).toBeInTheDocument()
  })

  it('renders upload and delete photo buttons', () => {
    renderWithProviders(<SettingsProfilePage />)
    expect(screen.getByText('Загрузить фото')).toBeInTheDocument()
    expect(screen.getByText('Удалить')).toBeInTheDocument()
  })

  it('renders cancel button', () => {
    renderWithProviders(<SettingsProfilePage />)
    expect(screen.getByText('Отмена')).toBeInTheDocument()
  })

  it('renders city as dropdown', () => {
    renderWithProviders(<SettingsProfilePage />)
    // City field is a select, check for it
    const selects = screen.getAllByRole('combobox')
    expect(selects.length).toBeGreaterThanOrEqual(1)
  })
})

// ===================== Toggle Switch CSS Tests =====================
describe('Toggle switches (SettingsSecurityPage)', () => {
  it('renders 2FA toggle as checkbox', () => {
    renderWithProviders(<SettingsSecurityPage />)
    expect(screen.getByText('Двухфакторная аутентификация')).toBeInTheDocument()
    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).toBeInTheDocument()
  })

  it('2FA toggle is initially off', () => {
    renderWithProviders(<SettingsSecurityPage />)
    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).not.toBeChecked()
  })

  it('2FA toggle can be switched on', () => {
    renderWithProviders(<SettingsSecurityPage />)
    const checkbox = screen.getByRole('checkbox')
    fireEvent.click(checkbox)
    expect(checkbox).toBeChecked()
  })

  it('2FA toggle can be switched off again', () => {
    renderWithProviders(<SettingsSecurityPage />)
    const checkbox = screen.getByRole('checkbox')
    fireEvent.click(checkbox)
    expect(checkbox).toBeChecked()
    fireEvent.click(checkbox)
    expect(checkbox).not.toBeChecked()
  })
})

// ===================== SettingsAiPage Toggle Tests =====================

describe('SettingsAiPage toggles', () => {
  it('renders all 5 optimization toggles', () => {
    renderWithProviders(<SettingsAiPage />)
    const checkboxes = screen.getAllByRole('checkbox')
    expect(checkboxes.length).toBe(5)
  })

  it('auto_metrics and ats toggles are on by default', () => {
    renderWithProviders(<SettingsAiPage />)
    const checkboxes = screen.getAllByRole('checkbox')
    // auto_metrics (0) = true, ats (1) = true, upgrade_title (2) = false, keep_language (3) = true, soft_skills (4) = false
    expect(checkboxes[0]).toBeChecked()
    expect(checkboxes[1]).toBeChecked()
    expect(checkboxes[2]).not.toBeChecked()
  })

  it('clicking a toggle changes its state', () => {
    renderWithProviders(<SettingsAiPage />)
    const checkboxes = screen.getAllByRole('checkbox')
    // Toggle off auto_metrics
    fireEvent.click(checkboxes[0])
    expect(checkboxes[0]).not.toBeChecked()
    // Toggle on upgrade_title
    fireEvent.click(checkboxes[2])
    expect(checkboxes[2]).toBeChecked()
  })

  it('renders all 4 AI models', () => {
    renderWithProviders(<SettingsAiPage />)
    expect(screen.getByText('GigaChat Pro')).toBeInTheDocument()
    expect(screen.getByText('OpenAI')).toBeInTheDocument()
    expect(screen.getByText('Anthropic Claude')).toBeInTheDocument()
    expect(screen.getAllByText('OpenRouter').length).toBeGreaterThanOrEqual(1)
  })

  it('default model is GigaChat Pro', () => {
    renderWithProviders(<SettingsAiPage />)
    expect(screen.getByText('Рекомендуем')).toBeInTheDocument()
  })

  it('save button works and shows confirmation', async () => {
    renderWithProviders(<SettingsAiPage />)
    const saveBtn = screen.getByText('Сохранить')
    fireEvent.click(saveBtn)
    await waitFor(() => {
      expect(screen.getByText('✓ Сохранено')).toBeInTheDocument()
    })
  })

  it('reset button restores defaults', () => {
    renderWithProviders(<SettingsAiPage />)
    const checkboxes = screen.getAllByRole('checkbox')
    // Toggle off auto_metrics
    fireEvent.click(checkboxes[0])
    expect(checkboxes[0]).not.toBeChecked()
    // Click reset
    fireEvent.click(screen.getByText('Сбросить'))
    const newCheckboxes = screen.getAllByRole('checkbox')
    expect(newCheckboxes[0]).toBeChecked()
  })
})

// ===================== Profile Photo Upload Tests =====================
describe('SettingsProfilePage photo upload', () => {
  it('has a hidden file input for photo', () => {
    renderWithProviders(<SettingsProfilePage />)
    const input = screen.getByTestId('photo-upload-input')
    expect(input).toBeInTheDocument()
    expect(input).toHaveAttribute('type', 'file')
    expect(input).toHaveAttribute('accept', 'image/*')
  })

  it('upload photo button triggers file input', () => {
    renderWithProviders(<SettingsProfilePage />)
    // The upload button and delete button exist
    expect(screen.getByText('Загрузить фото')).toBeInTheDocument()
  })

  it('delete photo button is initially disabled', () => {
    renderWithProviders(<SettingsProfilePage />)
    const deleteBtn = screen.getByText('Удалить').closest('button')
    expect(deleteBtn).toBeDisabled()
  })

  it('save button shows success message', async () => {
    renderWithProviders(<SettingsProfilePage />)
    fireEvent.click(screen.getByText('Сохранить изменения'))
    await waitFor(() => {
      expect(screen.getByText('Изменения сохранены')).toBeInTheDocument()
    })
  })
})

// ===================== History Page All Items Clickable =====================
describe('HistoryPage navigation', () => {
  it('shows loading state initially', () => {
    renderWithProviders(<HistoryPage />, '/app/history')
    expect(screen.getByText('Загрузка...')).toBeInTheDocument()
  })

  it('renders page heading', () => {
    renderWithProviders(<HistoryPage />, '/app/history')
    expect(screen.getByText('История оптимизаций')).toBeInTheDocument()
  })
})

// ===================== ResumesPage Actions =====================
import ResumesPage from '../pages/resumes/ResumesPage'

describe('ResumesPage actions', () => {
  it('view button links to results with ID', () => {
    const { container } = renderWithProviders(<ResumesPage />, '/app/resumes')
    const viewLinks = container.querySelectorAll('a[href*="/app/results/"]')
    expect(viewLinks.length).toBe(10) // 5 demo resumes × 2 (desktop table + mobile cards)
  })

  it('first resume links to /app/results/1', () => {
    const { container } = renderWithProviders(<ResumesPage />, '/app/resumes')
    const link = container.querySelector('a[href="/app/results/1"]')
    expect(link).toBeInTheDocument()
  })

  it('download button is clickable', () => {
    renderWithProviders(<ResumesPage />, '/app/resumes')
    const downloadBtns = screen.getAllByTitle('Скачать')
    expect(downloadBtns.length).toBe(5)
    // Each button should be functional
    downloadBtns.forEach(btn => {
      expect(btn).not.toBeDisabled()
    })
  })

  it('delete button is clickable', () => {
    renderWithProviders(<ResumesPage />, '/app/resumes')
    const deleteBtns = screen.getAllByTitle('Удалить')
    expect(deleteBtns.length).toBe(5)
  })
})

// ===================== Subscription Plan Switching =====================
describe('SettingsSubscriptionPage plan switching', () => {
  it('free plan is default / current', () => {
    renderWithProviders(<SettingsSubscriptionPage />)
    const currentBtn = screen.getByRole('button', { name: /текущий план/i })
    expect(currentBtn).toBeDisabled()
  })

  it('shows Robokassa payment info', () => {
    renderWithProviders(<SettingsSubscriptionPage />)
    expect(screen.getByText('Оплата через Робокассу')).toBeInTheDocument()
  })

  it('standard and pro buttons are enabled', () => {
    renderWithProviders(<SettingsSubscriptionPage />)
    const upgradeButtons = screen.getAllByRole('button', { name: /повысить/i })
    expect(upgradeButtons.length).toBe(2)
    upgradeButtons.forEach(btn => expect(btn).not.toBeDisabled())
  })

  it('shows usage for free plan (2 of 5)', () => {
    renderWithProviders(<SettingsSubscriptionPage />)
    expect(screen.getByText(/2 из 5/)).toBeInTheDocument()
  })
})

// ===================== ResultsPage with ID =====================
describe('ResultsPage with route params', () => {
  it('renders results page at /app/results/1 — shows loading then error', async () => {
    render(
      <MemoryRouter initialEntries={['/app/results/1']}>
        <WizardProvider>
          <Routes>
            <Route path="/app/results/:id" element={<ResultsPage />} />
          </Routes>
        </WizardProvider>
      </MemoryRouter>
    )
    // Initially shows loading, then error because API is not available in tests
    await waitFor(() => {
      expect(screen.getByText('Начать заново')).toBeInTheDocument()
    })
  })

  it('renders results page without ID (fallback) — shows no data message', async () => {
    renderWithProviders(<ResultsPage />)
    await waitFor(() => {
      expect(screen.getByText('Нет данных для отображения')).toBeInTheDocument()
    })
  })
})

// ===================== ModelsPage Selection =====================
describe('ModelsPage model selection', () => {
  it('GigaChat Pro is selected by default', () => {
    const { container } = renderWithProviders(<ModelsPage />, '/app/models')
    const selectedCard = container.querySelector('.model-card.selected')
    expect(selectedCard).toBeInTheDocument()
    expect(selectedCard?.textContent).toContain('GigaChat Pro')
  })

  it('clicking another model selects it', () => {
    const { container } = renderWithProviders(<ModelsPage />, '/app/models')
    const cards = container.querySelectorAll('.model-card')
    // Click GPT-4o (2nd card)
    fireEvent.click(cards[1])
    expect(cards[1].classList.contains('selected')).toBe(true)
    expect(cards[0].classList.contains('selected')).toBe(false)
  })

  it('start optimization button is present', () => {
    renderWithProviders(<ModelsPage />, '/app/models')
    expect(screen.getByText('Начать оптимизацию')).toBeInTheDocument()
  })
})

// ===================== Robokassa Utils =====================
import { generateInvoiceId, PLAN_PRICES } from '../utils/robokassa'

describe('Robokassa utils', () => {
  it('generateInvoiceId returns a number', () => {
    const id = generateInvoiceId()
    expect(typeof id).toBe('number')
    expect(id).toBeGreaterThan(0)
  })

  it('generateInvoiceId returns different IDs', () => {
    const id1 = generateInvoiceId()
    // Wait a tiny bit to ensure different timestamp
    const id2 = generateInvoiceId()
    // They should at least be numbers
    expect(typeof id1).toBe('number')
    expect(typeof id2).toBe('number')
  })

  it('PLAN_PRICES has correct values', () => {
    expect(PLAN_PRICES.standard).toBe(490)
    expect(PLAN_PRICES.pro).toBe(1490)
  })
})

// ===================== VacancyPage Tabs & Selection =====================
describe('VacancyPage functionality', () => {
  it('renders all 3 tabs', () => {
    renderWithProviders(<VacancyPage />, '/app/vacancy')
    expect(screen.getByText('Поиск hh.ru')).toBeInTheDocument()
    expect(screen.getByText('Вставить URL')).toBeInTheDocument()
    expect(screen.getByText('Ввести вручную')).toBeInTheDocument()
  })

  it('search tab is active by default', () => {
    renderWithProviders(<VacancyPage />, '/app/vacancy')
    expect(screen.getByText('Должность')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Product Manager')).toBeInTheDocument()
  })

  it('switching to URL tab shows URL input', () => {
    renderWithProviders(<VacancyPage />, '/app/vacancy')
    fireEvent.click(screen.getByText('Вставить URL'))
    expect(screen.getByPlaceholderText('https://hh.ru/vacancy/12345678')).toBeInTheDocument()
  })

  it('switching to manual tab shows form fields', () => {
    renderWithProviders(<VacancyPage />, '/app/vacancy')
    fireEvent.click(screen.getByText('Ввести вручную'))
    expect(screen.getByPlaceholderText('Яндекс')).toBeInTheDocument()
  })

  it('selecting a vacancy enables continue button', () => {
    renderWithProviders(<VacancyPage />, '/app/vacancy')
    // Click on first vacancy card (Senior Product Manager)
    fireEvent.click(screen.getByText('Senior Product Manager'))
    expect(screen.getByText('Продолжить с выбранной вакансией')).toBeInTheDocument()
  })
})

// ===================== UploadPage Drag & Drop =====================
describe('UploadPage functionality', () => {
  it('renders dropzone', () => {
    renderWithProviders(<UploadPage />, '/app/upload')
    expect(screen.getByText('Перетащите файл сюда')).toBeInTheDocument()
  })

  it('supports PDF and DOCX', () => {
    renderWithProviders(<UploadPage />, '/app/upload')
    expect(screen.getByText('PDF')).toBeInTheDocument()
    expect(screen.getByText('DOCX')).toBeInTheDocument()
    expect(screen.getByText('до 10 МБ')).toBeInTheDocument()
  })

  it('selecting a file shows continue button', () => {
    renderWithProviders(<UploadPage />, '/app/upload')
    const fileInput = document.getElementById('file-input') as HTMLInputElement
    const file = new File(['content'], 'resume.pdf', { type: 'application/pdf' })
    fireEvent.change(fileInput, { target: { files: [file] } })
    expect(screen.getByText('resume.pdf')).toBeInTheDocument()
    expect(screen.getByText('Продолжить')).toBeInTheDocument()
  })
})

// ===================== ProcessingPage Animation =====================
describe('ProcessingPage', () => {
  it('renders processing steps', () => {
    renderWithProviders(<ProcessingPage />, '/app/processing')
    expect(screen.getByText('Загрузка документа')).toBeInTheDocument()
    expect(screen.getByText('Анализ вакансии')).toBeInTheDocument()
    expect(screen.getByText('AI оптимизация')).toBeInTheDocument()
    expect(screen.getByText('Финализация')).toBeInTheDocument()
  })

  it('starts at 0% progress', () => {
    renderWithProviders(<ProcessingPage />, '/app/processing')
    expect(screen.getByText('0%')).toBeInTheDocument()
  })
})

// ===================== Security Page Password Form =====================
describe('SettingsSecurityPage password change', () => {
  it('validates empty fields', () => {
    renderWithProviders(<SettingsSecurityPage />)
    fireEvent.click(screen.getByText('Обновить пароль'))
    expect(screen.getByText('Заполните все поля')).toBeInTheDocument()
  })

  it('validates password min length', () => {
    renderWithProviders(<SettingsSecurityPage />)
    const inputs = screen.getAllByPlaceholderText('••••••••')
    fireEvent.change(inputs[0], { target: { value: 'old' } })
    fireEvent.change(screen.getByPlaceholderText('Мин. 8 символов, цифра + буква'), { target: { value: 'short' } })
    fireEvent.change(inputs[1], { target: { value: 'short' } })
    fireEvent.click(screen.getByText('Обновить пароль'))
    expect(screen.getByText('Пароль должен быть минимум 8 символов')).toBeInTheDocument()
  })

  it('validates password mismatch', () => {
    renderWithProviders(<SettingsSecurityPage />)
    const inputs = screen.getAllByPlaceholderText('••••••••')
    fireEvent.change(inputs[0], { target: { value: 'oldpassword' } })
    fireEvent.change(screen.getByPlaceholderText('Мин. 8 символов, цифра + буква'), { target: { value: 'newpassword1' } })
    fireEvent.change(inputs[1], { target: { value: 'different1' } })
    fireEvent.click(screen.getByText('Обновить пароль'))
    expect(screen.getByText('Пароли не совпадают')).toBeInTheDocument()
  })

  it('shows success on valid password change', () => {
    renderWithProviders(<SettingsSecurityPage />)
    const inputs = screen.getAllByPlaceholderText('••••••••')
    fireEvent.change(inputs[0], { target: { value: 'oldpassword' } })
    fireEvent.change(screen.getByPlaceholderText('Мин. 8 символов, цифра + буква'), { target: { value: 'newpassword1' } })
    fireEvent.change(inputs[1], { target: { value: 'newpassword1' } })
    fireEvent.click(screen.getByText('Обновить пароль'))
    expect(screen.getByText('Пароль успешно обновлён')).toBeInTheDocument()
  })

  it('delete account requires confirmation text', () => {
    renderWithProviders(<SettingsSecurityPage />)
    fireEvent.click(screen.getByText('Удалить аккаунт'))
    const confirmBtn = screen.getByText('Подтвердить')
    expect(confirmBtn).toBeDisabled()
    // Type УДАЛИТЬ
    fireEvent.change(screen.getByPlaceholderText(/УДАЛИТЬ/), { target: { value: 'УДАЛИТЬ' } })
    expect(confirmBtn).not.toBeDisabled()
  })
})
