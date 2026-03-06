import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'

/* eslint-disable @typescript-eslint/no-explicit-any */
export interface RewriteResult {
  id: string
  resume_id: string | null
  vacancy_id: string | null
  status: string
  match_score_before: number | null
  match_score_after: number | null
  ats_rating: string | null
  model_name: string | null
  processing_time_ms: number | null
  original_text: string | null
  rewritten_text: string | null
  rewritten_data: any
  keywords_added: string[] | null
  tokens_used: number | null
  error_message: string | null
  created_at: string | null
  score_breakdown?: {
    keywords?: number
    experience?: number
    structure?: number
    readability?: number
  }
}

interface WizardState {
  file: File | null
  resumeId: string | null
  vacancyId: string | null
  model: string
  taskId: string | null
  result: RewriteResult | null
}

interface WizardContextType extends WizardState {
  setFile: (file: File | null) => void
  setResumeId: (id: string | null) => void
  setVacancyId: (id: string | null) => void
  setModel: (model: string) => void
  setTaskId: (id: string | null) => void
  setResult: (result: RewriteResult | null) => void
  reset: () => void
}

const DEFAULT_STATE: WizardState = {
  file: null,
  resumeId: null,
  vacancyId: null,
  model: 'gigachat-pro',
  taskId: null,
  result: null,
}

const WizardContext = createContext<WizardContextType | null>(null)

export function WizardProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<WizardState>(DEFAULT_STATE)

  const setFile = useCallback((file: File | null) => setState(s => ({ ...s, file })), [])
  const setResumeId = useCallback((resumeId: string | null) => setState(s => ({ ...s, resumeId })), [])
  const setVacancyId = useCallback((vacancyId: string | null) => setState(s => ({ ...s, vacancyId })), [])
  const setModel = useCallback((model: string) => setState(s => ({ ...s, model })), [])
  const setTaskId = useCallback((taskId: string | null) => setState(s => ({ ...s, taskId })), [])
  const setResult = useCallback((result: RewriteResult | null) => setState(s => ({ ...s, result })), [])
  const reset = useCallback(() => setState(DEFAULT_STATE), [])

  return (
    <WizardContext.Provider value={{ ...state, setFile, setResumeId, setVacancyId, setModel, setTaskId, setResult, reset }}>
      {children}
    </WizardContext.Provider>
  )
}

export function useWizard() {
  const context = useContext(WizardContext)
  if (!context) throw new Error('useWizard must be used within WizardProvider')
  return context
}
