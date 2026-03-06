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

    // UI-005: Автоматический refresh при 401
    if (res.status === 401 && !path.includes('/auth/refresh') && !path.includes('/auth/login')) {
      const refreshed = await this.tryRefreshToken()
      if (refreshed) {
        // Повторяем исходный запрос с новым токеном
        const retry = await fetch(`${API_BASE}${path}`, {
          method,
          headers: this.headers(),
          body: body ? JSON.stringify(body) : undefined,
        })
        if (!retry.ok) {
          const err = await retry.json().catch(() => ({ message: retry.statusText }))
          throw new Error(err.message || err.detail || retry.statusText)
        }
        if (retry.status === 204) return undefined as T
        return retry.json()
      }
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: res.statusText }))
      throw new Error(err.message || err.detail || res.statusText)
    }
    if (res.status === 204) return undefined as T
    return res.json()
  }

  private async tryRefreshToken(): Promise<boolean> {
    try {
      const rt = localStorage.getItem('refresh_token')
      if (!rt) return false
      const data = await this.refreshToken(rt)
      this.setToken(data.access_token)
      if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
      return true
    } catch {
      this.clearToken()
      localStorage.removeItem('refresh_token')
      return false
    }
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
    const res = await this.request<{ items: unknown[]; total: number } | unknown[]>('GET', '/resumes')
    return Array.isArray(res) ? res : (res as any).items || []
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

  async getModels() {
    return this.request<{ models: Array<{ id: string; name: string; provider: string; available: boolean; description: string; has_sub_models?: boolean; sub_models?: Array<{ id: string; name: string; provider: string }> }> }>('GET', '/models')
  }

  async getSubModels(provider: string) {
    return this.request<{ sub_models: Array<{ id: string; name: string; provider: string }>; error?: string; fallback?: boolean }>('GET', `/models/${provider}/sub-models`)
  }

  async startRewrite(resumeId: string, vacancyId: string, model: string, subModel?: string) {
    return this.request<{ task_id: string }>('POST', '/rewrite', {
      resume_id: resumeId, vacancy_id: vacancyId, model,
      ...(subModel ? { sub_model: subModel } : {}),
    })
  }

  async getRewriteStatus(taskId: string) {
    return this.request<{ status: string; step: string; progress: number; error_message?: string }>('GET', `/rewrite/${taskId}/status`)
  }

  async getRewriteResult(taskId: string) {
    return this.request<unknown>('GET', `/rewrite/${taskId}/result`)
  }

  async getRewriteHistory() {
    const res = await this.request<{ items: unknown[]; total: number } | unknown[]>('GET', '/rewrite/history')
    return Array.isArray(res) ? res : (res as any).items || []
  }

  async exportDocx(id: string) {
    const tok = this.token || localStorage.getItem('access_token')
    const res = await fetch(`${API_BASE}/export/${id}/docx`, {
      headers: tok ? { 'Authorization': `Bearer ${tok}` } : {},
    })
    if (!res.ok) throw new Error('Export failed')
    return res.blob()
  }

  async downloadResumeFile(id: string) {
    const tok = this.token || localStorage.getItem('access_token')
    const res = await fetch(`${API_BASE}/resumes/${id}/file`, {
      headers: tok ? { 'Authorization': `Bearer ${tok}` } : {},
    })
    if (!res.ok) throw new Error('Download failed')
    return res.blob()
  }

  // --- Missing methods ---

  async refreshToken(refreshToken: string) {
    return this.request<{ access_token: string; refresh_token: string; token_type: string }>(
      'POST', '/auth/refresh', { refresh_token: refreshToken }
    )
  }

  async serverLogout(refreshToken: string) {
    return this.request<void>('POST', '/auth/logout', { refresh_token: refreshToken })
  }

  async updateProfile(data: { full_name?: string; email?: string }) {
    return this.request<{
      id: string; email: string; full_name: string | null;
      plan: 'free' | 'standard' | 'pro'; optimizations_used: number; is_active: boolean
    }>('PUT', '/auth/me', data)
  }

  async changePassword(data: { current_password: string; new_password: string }) {
    return this.request<{ message: string }>('PUT', '/auth/me/password', data)
  }

  async getResume(id: string) {
    return this.request<Record<string, unknown>>('GET', `/resumes/${id}`)
  }

  async updateResume(id: string, data: Record<string, unknown>) {
    return this.request<Record<string, unknown>>('PUT', `/resumes/${id}`, data)
  }

  async deleteResume(id: string) {
    return this.request<void>('DELETE', `/resumes/${id}`)
  }

  async getVacancy(id: string) {
    return this.request<Record<string, unknown>>('GET', `/vacancies/${id}`)
  }

  async getHHVacancyDetail(hhId: string) {
    return this.request<Record<string, unknown>>('GET', `/vacancies/hh/${hhId}`)
  }

  async deleteVacancy(id: string) {
    return this.request<void>('DELETE', `/vacancies/${id}`)
  }

  async createResumeFromText(data: { text: string; title?: string; source_url?: string }) {
    return this.request<{ id: string; title: string; file_format: string; status: string }>(
      'POST', '/resumes/from-text', data
    )
  }

  async parseResumeFromUrl(url: string) {
    return this.request<{ id: string; title: string; file_format: string; status: string; raw_text?: string }>(
      'POST', '/resumes/from-url', { url }
    )
  }

  async deleteAccount(password: string) {
    return this.request<{ message: string }>('DELETE', '/auth/me', { password })
  }

  // --- Settings API ---
  async getAIKeys() {
    return this.request<{ keys: Array<{ provider: string; has_key: boolean; masked_key: string }> }>('GET', '/settings/ai-keys')
  }

  async saveAIKey(provider: string, apiKey: string) {
    return this.request<{ provider: string; has_key: boolean; masked_key: string }>('PUT', `/settings/ai-keys/${provider}`, { api_key: apiKey })
  }

  async deleteAIKey(provider: string) {
    return this.request<void>('DELETE', `/settings/ai-keys/${provider}`)
  }

  async getAIToggles() {
    return this.request<{ toggles: Record<string, boolean> }>('GET', '/settings/ai-toggles')
  }

  async saveAIToggles(toggles: Array<{ key: string; value: boolean }>) {
    return this.request<{ toggles: Record<string, boolean> }>('PUT', '/settings/ai-toggles', { toggles })
  }

  async getSelectedModel() {
    return this.request<{ model: string; sub_model: string | null }>('GET', '/settings/ai-model')
  }

  async saveSelectedModel(model: string, subModel?: string) {
    return this.request<{ model: string; sub_model: string | null }>('PUT', '/settings/ai-model', { model, sub_model: subModel || null })
  }

  /** @deprecated Используйте createVacancyFromUrl. Оставлено для обратной совместимости. */
  async selectSearchVacancy(hhUrl: string) {
    return this.createVacancyFromUrl(hhUrl)
  }
}

export const api = new ApiClient()
