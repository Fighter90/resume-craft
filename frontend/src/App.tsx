import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import { WizardProvider } from './contexts/WizardContext'

// Layouts
import AppLayout from './components/layout/AppLayout'
import PublicLayout from './components/layout/PublicLayout'
import CenteredLayout from './components/layout/CenteredLayout'

// Public pages
import LandingPage from './pages/LandingPage'
import AuthPage from './pages/auth/AuthPage'
import PasswordRecoveryPage from './pages/auth/PasswordRecoveryPage'
import EmailVerifyPage from './pages/auth/EmailVerifyPage'
import PricingPage from './pages/PricingPage'
import PrivacyPage from './pages/PrivacyPage'
import TermsPage from './pages/TermsPage'
import AboutPage from './pages/AboutPage'
import ErrorPage from './pages/ErrorPage'

// App pages
import DashboardPage from './pages/dashboard/DashboardPage'
import ResumesPage from './pages/resumes/ResumesPage'
import UploadPage from './pages/wizard/UploadPage'
import VacancyPage from './pages/wizard/VacancyPage'
import ModelsPage from './pages/wizard/ModelsPage'
import ProcessingPage from './pages/wizard/ProcessingPage'
import ResultsPage from './pages/wizard/ResultsPage'
import EditorPage from './pages/wizard/EditorPage'
import ExportPage from './pages/wizard/ExportPage'
import HistoryPage from './pages/history/HistoryPage'

// Settings
import SettingsLayout from './pages/settings/SettingsLayout'
import SettingsProfilePage from './pages/settings/SettingsProfilePage'
import SettingsAiPage from './pages/settings/SettingsAiPage'
import SettingsSubscriptionPage from './pages/settings/SettingsSubscriptionPage'
import SettingsSecurityPage from './pages/settings/SettingsSecurityPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { loading, isAuthenticated } = useAuth()
  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div className="processing-spinner" />
      </div>
    )
  }
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />
  }
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/about" element={<AboutPage />} />
      </Route>

      {/* Centered routes */}
      <Route element={<CenteredLayout />}>
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/password-recovery" element={<PasswordRecoveryPage />} />
        <Route path="/email-verify" element={<EmailVerifyPage />} />
      </Route>

      {/* Protected app routes */}
      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <WizardProvider>
              <AppLayout />
            </WizardProvider>
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="resumes" element={<ResumesPage />} />
        <Route path="upload" element={<UploadPage />} />
        <Route path="vacancy" element={<VacancyPage />} />
        <Route path="models" element={<ModelsPage />} />
        <Route path="processing" element={<ProcessingPage />} />
        <Route path="results" element={<ResultsPage />} />
        <Route path="results/:id" element={<ResultsPage />} />
        <Route path="editor" element={<EditorPage />} />
        <Route path="export" element={<ExportPage />} />
        <Route path="export/:id" element={<ExportPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="settings" element={<SettingsLayout />}>
          <Route index element={<Navigate to="profile" replace />} />
          <Route path="profile" element={<SettingsProfilePage />} />
          <Route path="ai" element={<SettingsAiPage />} />
          <Route path="subscription" element={<SettingsSubscriptionPage />} />
          <Route path="security" element={<SettingsSecurityPage />} />
        </Route>
      </Route>

      {/* 404 */}
      <Route path="*" element={<ErrorPage />} />
    </Routes>
  )
}
