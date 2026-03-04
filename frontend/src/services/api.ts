const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export class ApiClient {
  private token: string | null = null

  setToken(token: string | null) {
    this.token = token
    if (token) localStorage.setItem('access_token', token)
  }

  clearToken() {
    this.token = null
    localStorage.removeItem('access_token')
  }

  private headers(): Record<string, string> {
    const h: Record<string, string> = { 'Content-Type': 'application/json' }
    const tok = this.token || localStorage.getItem('access_token')
    if (tok) h['Authorization'] = `Bearer ${tok}`
    return h
  }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers: this.headers(),
      body: body ? JSON.stringify(body) : undefined,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: res.statusText }))
      throw new Error(err.message || err.detail || res.statusText)
    }
    if (res.status === 204) return undefined as T
    return res.json()
  }

  async login(email: string, password: string) {
    return this.request<{ access_token: string; refresh_token: string; token_type: string }>(
      'POST', '/auth/login', { email, password }
    )
  }

  async register(email: string, password: string, fullName?: string) {
    return this.request<{ access_token: string; refresh_token: string; token_type: string }>(
      'POST', '/auth/register', { email, password, full_name: fullName }
    )
  }

  async healthCheck() {
    return this.request<{ status: string }>('GET', '/health')
  }

  async getMe() {
    return this.request<{
      id: string; email: string; full_name: string | null;
      plan: 'free' | 'standard' | 'pro'; optimizations_used: number; is_active: boolean
    }>('GET', '/auth/me')
  }

  async getResumes() {
    return this.request<unknown[]>('GET', '/resumes')
  }

  async uploadResume(file: File) {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${API_BASE}/resumes/upload`, {
      method: 'POST',
      headers: this.token ? { 'Authorization': `Bearer ${this.token}` } : {},
      body: form,
    })
    if (!res.ok) throw new Error('Upload failed')
    return res.json()
  }

  async searchVacancies(params: Record<string, string>) {
    const qs = new URLSearchParams(params).toString()
    return this.request<unknown[]>('GET', `/vacancies/search?${qs}`)
  }

  async createVacancyFromUrl(url: string) {
    return this.request<unknown>('POST', '/vacancies/from-url', { url })
  }

  async createVacancyManual(data: { title: string; company?: string; description: string; key_skills?: string[] }) {
    return this.request<unknown>('POST', '/vacancies/manual', data)
  }

  async startRewrite(resumeId: string, vacancyId: string, model: string) {
    return this.request<{ task_id: string }>('POST', '/rewrite', {
      resume_id: resumeId, vacancy_id: vacancyId, model,
    })
  }

  async getRewriteStatus(taskId: string) {
    return this.request<{ status: string; step: string; progress: number }>('GET', `/rewrite/${taskId}/status`)
  }

  async getRewriteResult(taskId: string) {
    return this.request<unknown>('GET', `/rewrite/${taskId}/result`)
  }

  async getRewriteHistory() {
    return this.request<unknown[]>('GET', '/rewrite/history')
  }

  async exportDocx(id: string) {
    const res = await fetch(`${API_BASE}/export/${id}/docx`, {
      headers: this.token ? { 'Authorization': `Bearer ${this.token}` } : {},
    })
    if (!res.ok) throw new Error('Export failed')
    return res.blob()
  }
}

export const api = new ApiClient()
