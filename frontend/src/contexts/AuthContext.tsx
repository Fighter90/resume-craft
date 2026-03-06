import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'
import { api } from '../services/api'

interface User {
  id: string
  email: string
  full_name: string | null
  plan: 'free' | 'standard' | 'pro'
  optimizations_used: number
  is_active: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'))
  const [loading, setLoading] = useState(true)

  const logout = useCallback(() => {
    // Call server-side logout to invalidate refresh token
    const rt = localStorage.getItem('refresh_token')
    if (rt) {
      api.serverLogout(rt).catch(() => {/* ignore errors on logout */})
    }
    setUser(null)
    setToken(null)
    api.clearToken()
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('ai_settings')
  }, [])

  const refreshUser = useCallback(async () => {
    try {
      const me = await api.getMe()
      setUser(me)
    } catch {
      // If getMe fails, token may be expired
      logout()
    }
  }, [logout])

  useEffect(() => {
    if (token) {
      api.setToken(token)
      api.getMe()
        .then(setUser)
        .catch(() => logout())
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [token, logout])

  const login = async (email: string, password: string) => {
    const data = await api.login(email, password)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    setToken(data.access_token)
    api.setToken(data.access_token)
    const me = await api.getMe()
    setUser(me)
  }

  const register = async (email: string, password: string, fullName?: string) => {
    const data = await api.register(email, password, fullName)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    setToken(data.access_token)
    api.setToken(data.access_token)
    const me = await api.getMe()
    setUser(me)
  }

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
