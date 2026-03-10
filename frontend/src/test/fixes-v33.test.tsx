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
  it('does not block sub-models loading by available flag', async () => {
    const src = await readSource('src/pages/wizard/ModelsPage.tsx')
    // useEffect должен проверять только has_sub_models, а НЕ available
    expect(src).toContain('if (!selectedModel?.has_sub_models) {')
    // Убедимся что нет блокирующей проверки || !selectedModel.available
    const lines = src.split('\n')
    let foundCheck = false
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('if (!selectedModel?.has_sub_models')) {
        const block = lines.slice(i, i + 3).join('\n')
        expect(block).not.toContain('|| !selectedModel.available')
        foundCheck = true
        break
      }
    }
    expect(foundCheck).toBe(true)
  })
})

describe('VACANCY-PLACEHOLDER-001: VacancyPage', () => {
  it('directly sets manual title from resume without fallback', async () => {
    const src = await readSource('src/pages/wizard/VacancyPage.tsx')
    expect(src).toContain('api.getResume(resumeId)')
    // Проверяем что используется прямое присвоение, а не callback с prev
    expect(src).toContain('setManualTitle(defaultTitle)')
    expect(src).toContain('parsed.position')
    expect(src).toContain('parsed.target_position')
    expect(src).toContain('parsed.desired_position')
  })
})
