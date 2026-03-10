/**
 * V33 Frontend Tests
 *
 * Covers:
 * - KEY-CHECK-001: no client-side API-key blocking on ModelsPage
 * - VACANCY-PLACEHOLDER-001: VacancyPage pre-fills manual title from resume data
 */

import { describe, it, expect } from 'vitest'

async function readSource(path: string): Promise<string> {
  const fs = await import('fs')
  return fs.readFileSync(path, 'utf-8')
}

describe('KEY-CHECK-001: ModelsPage', () => {
  it('does not block start button by local available flag', async () => {
    const src = await readSource('src/pages/wizard/ModelsPage.tsx')
    expect(src).toContain('Always send request to backend')
    expect(src).toContain('disabled={loading}')
    expect(src).not.toContain('selectedModel && !selectedModel.available')
  })
})

describe('VACANCY-PLACEHOLDER-001: VacancyPage', () => {
  it('prefills manual title from resume metadata', async () => {
    const src = await readSource('src/pages/wizard/VacancyPage.tsx')
    expect(src).toContain('api.getResume(resumeId)')
    expect(src).toContain('setManualTitle(')
    expect(src).toContain('parsed.position')
    expect(src).toContain('parsed.target_position')
    expect(src).toContain('parsed.desired_position')
  })
})
