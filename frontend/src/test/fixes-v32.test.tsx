/**
 * V32 Frontend Tests
 *
 * Covers:
 * - PRICING-MISMATCH-001: BYOK text alignment across pricing pages
 * - HISTORY-COUNT-001: dashboard success/attempts hint
 */

import { describe, expect, it } from 'vitest'

async function readSource(path: string): Promise<string> {
  const fs = await import('fs')
  return fs.readFileSync(path, 'utf-8')
}

describe('PRICING-MISMATCH-001', () => {
  it('uses BYOK wording on landing, pricing and subscription pages', async () => {
    const landing = await readSource('src/pages/LandingPage.tsx')
    const pricing = await readSource('src/pages/PricingPage.tsx')
    const subscription = await readSource('src/pages/settings/SettingsSubscriptionPage.tsx')

    expect(landing).toContain('Все AI-модели (BYOK)')
    expect(pricing).toContain('Все AI-модели (BYOK)')
    expect(subscription).toContain('Все AI-модели (BYOK)')

    expect(landing).not.toContain("'OpenRouter'")
    expect(pricing).not.toContain("'OpenRouter'")
  })
})

describe('HISTORY-COUNT-001', () => {
  it('shows successful optimizations out of attempts on dashboard', async () => {
    const dashboard = await readSource('src/pages/dashboard/DashboardPage.tsx')
    expect(dashboard).toContain('const totalAttempts = history.length')
    expect(dashboard).toContain('Успешных: {totalOptimizations} из {totalAttempts}')
  })
})
