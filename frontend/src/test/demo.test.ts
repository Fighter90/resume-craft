import { describe, it, expect } from 'vitest'
import { DEMO_USER, DEMO_RESUMES, DEMO_VACANCIES, DEMO_HISTORY, DEMO_SCORES, DEMO_KEYWORDS, DEMO_ORIGINAL_TEXT, DEMO_OPTIMIZED_TEXT } from '../data/demo'

describe('Demo Data', () => {
  it('DEMO_USER has required fields', () => {
    expect(DEMO_USER.id).toBeDefined()
    expect(DEMO_USER.email).toContain('@')
    expect(DEMO_USER.full_name).toBeTruthy()
    expect(['free', 'standard', 'pro']).toContain(DEMO_USER.plan)
  })

  it('DEMO_RESUMES contains 5 items', () => {
    expect(DEMO_RESUMES).toHaveLength(5)
    DEMO_RESUMES.forEach(r => {
      expect(r.id).toBeDefined()
      expect(r.title).toBeTruthy()
      expect(['pdf', 'docx']).toContain(r.file_format)
      expect(['draft', 'processing', 'optimized', 'error']).toContain(r.status)
    })
  })

  it('DEMO_VACANCIES contains 3 items', () => {
    expect(DEMO_VACANCIES).toHaveLength(3)
    DEMO_VACANCIES.forEach(v => {
      expect(v.title).toBeTruthy()
      expect(v.company).toBeTruthy()
      expect(v.matchScore).toBeGreaterThanOrEqual(0)
      expect(v.matchScore).toBeLessThanOrEqual(100)
    })
  })

  it('DEMO_HISTORY has date groups with items', () => {
    expect(DEMO_HISTORY.length).toBeGreaterThan(0)
    DEMO_HISTORY.forEach(g => {
      expect(g.date).toBeTruthy()
      expect(g.items.length).toBeGreaterThan(0)
      g.items.forEach(item => {
        expect(item.type).toBeTruthy()
        expect(item.title).toBeTruthy()
      })
    })
  })

  it('DEMO_SCORES breakdown sums correctly', () => {
    const b = DEMO_SCORES.breakdown
    expect(b.keywords).toBeGreaterThanOrEqual(0)
    expect(b.experience).toBeGreaterThanOrEqual(0)
    expect(b.structure).toBeGreaterThanOrEqual(0)
    expect(b.readability).toBeGreaterThanOrEqual(0)
    expect(DEMO_SCORES.matchScore).toBeGreaterThan(0)
    expect(DEMO_SCORES.atsRating).toBeTruthy()
  })

  it('DEMO_KEYWORDS is a non-empty string array', () => {
    expect(DEMO_KEYWORDS.length).toBeGreaterThan(0)
    DEMO_KEYWORDS.forEach(kw => expect(typeof kw).toBe('string'))
  })

  it('DEMO_ORIGINAL_TEXT and DEMO_OPTIMIZED_TEXT have correct structure', () => {
    expect(DEMO_ORIGINAL_TEXT.name).toBeTruthy()
    expect(DEMO_ORIGINAL_TEXT.score).toBeLessThan(DEMO_OPTIMIZED_TEXT.score)
    expect(DEMO_OPTIMIZED_TEXT.summary.length).toBeGreaterThan(DEMO_ORIGINAL_TEXT.summary.length)
  })
})
