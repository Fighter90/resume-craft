import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          minHeight: '60vh', padding: '2rem', textAlign: 'center',
        }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.75rem' }}>
            Что-то пошло не так
          </h2>
          <p style={{ color: '#6B7280', marginBottom: '1.5rem', maxWidth: 480 }}>
            Произошла непредвиденная ошибка. Попробуйте обновить страницу.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button
              className="btn btn-primary"
              onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload() }}
            >
              Обновить страницу
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => { this.setState({ hasError: false, error: null }); window.location.href = '/app/dashboard' }}
            >
              На главную
            </button>
          </div>
          {this.state.error && (
            <details style={{ marginTop: '1.5rem', fontSize: '0.8rem', color: '#9CA3AF', maxWidth: 600, textAlign: 'left' }}>
              <summary style={{ cursor: 'pointer' }}>Детали ошибки</summary>
              <pre style={{ whiteSpace: 'pre-wrap', marginTop: '0.5rem' }}>{this.state.error.message}</pre>
            </details>
          )}
        </div>
      )
    }

    return this.props.children
  }
}
