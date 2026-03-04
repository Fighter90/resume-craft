import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Download, Sparkles, Save, User, Briefcase, GraduationCap, Star, FileText, X, Plus, Loader } from 'lucide-react'
import { useWizard } from '../../contexts/WizardContext'
import { api } from '../../services/api'

/* eslint-disable @typescript-eslint/no-explicit-any */

const SECTIONS = [
  { id: 'header', label: 'Заголовок', icon: User },
  { id: 'experience', label: 'Опыт работы', icon: Briefcase },
  { id: 'education', label: 'Образование', icon: GraduationCap },
  { id: 'skills', label: 'Навыки', icon: Star },
  { id: 'about', label: 'О себе', icon: FileText },
]

const CHAR_LIMITS: Record<string, { min: number; max: number }> = {
  header: { min: 50, max: 300 },
  experience: { min: 200, max: 2000 },
  education: { min: 50, max: 500 },
  skills: { min: 30, max: 300 },
  about: { min: 100, max: 500 },
}

const AI_HINTS = [
  { type: 'metric', color: '#D97706', bg: '#FEF3C7', title: 'Добавьте метрики', text: 'Укажите конкретные числа: рост в %, количество проектов, размер команды' },
  { type: 'keyword', color: 'var(--primary)', bg: 'rgba(86,90,221,0.08)', title: 'Ключевое слово', text: 'Добавьте «Product Strategy» — встречается в 89% аналогичных вакансий' },
  { type: 'format', color: 'var(--success)', bg: 'rgba(16,185,129,0.08)', title: 'Формулировка', text: 'Используйте формулу: Действие + Результат + Метрика' },
]

export default function EditorPage() {
  const navigate = useNavigate()
  const { result, resumeId } = useWizard()
  const [activeSection, setActiveSection] = useState('header')
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)

  // Initialize state from result.rewritten_data if available
  const rd = result?.rewritten_data as any
  const [headerData, setHeaderData] = useState({
    fullName: rd?.summary?.split('.')[0] || '',
    position: rd?.experience?.[0]?.position || '',
    email: '',
    phone: '',
    city: '',
    linkedin: '',
  })
  const [experiences, setExperiences] = useState<Array<{ position: string; company: string; period: string; achievements: string }>>(
    rd?.experience?.map((e: any) => ({
      position: e.position || '',
      company: e.company || '',
      period: e.period || '',
      achievements: Array.isArray(e.achievements) ? e.achievements.join('\n') : (e.achievements || ''),
    })) || [{ position: '', company: '', period: '', achievements: '' }]
  )
  const [educations, setEducations] = useState<Array<{ institution: string; specialization: string; degree: string; year: string }>>(
    rd?.education?.map((e: any) => ({
      institution: e.institution || '',
      specialization: e.specialization || '',
      degree: e.degree || 'Бакалавриат',
      year: String(e.year || ''),
    })) || [{ institution: '', specialization: '', degree: 'Бакалавриат', year: '' }]
  )
  const [skills, setSkills] = useState<string[]>(rd?.skills || [])
  const [aiSkills] = useState<string[]>(result?.keywords_added || [])
  const [newSkill, setNewSkill] = useState('')
  const [aboutText, setAboutText] = useState(rd?.summary || result?.rewritten_text?.slice(0, 500) || '')

  // Reload from result if it changes
  useEffect(() => {
    if (rd) {
      if (rd.experience) setExperiences(rd.experience.map((e: any) => ({
        position: e.position || '', company: e.company || '', period: e.period || '',
        achievements: Array.isArray(e.achievements) ? e.achievements.join('\n') : (e.achievements || ''),
      })))
      if (rd.education) setEducations(rd.education.map((e: any) => ({
        institution: e.institution || '', specialization: e.specialization || '',
        degree: e.degree || 'Бакалавриат', year: String(e.year || ''),
      })))
      if (rd.skills) setSkills(rd.skills)
      if (rd.summary) setAboutText(rd.summary)
    }
  }, [result]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSave = async () => {
    if (!resumeId) return
    setSaving(true)
    setSaveMsg(null)
    try {
      const data = {
        title: headerData.position || 'Резюме',
        parsed_data: {
          header: headerData,
          experience: experiences,
          education: educations,
          skills: [...skills, ...aiSkills],
          about: aboutText,
        },
      }
      await api.updateResume(resumeId, data)
      setSaveMsg('Черновик сохранён')
      setTimeout(() => setSaveMsg(null), 3000)
    } catch (err) {
      setSaveMsg(err instanceof Error ? err.message : 'Ошибка сохранения')
    } finally {
      setSaving(false)
    }
  }

  const getCharCount = () => {
    switch (activeSection) {
      case 'header': return Object.values(headerData).join('').length
      case 'experience': return experiences.map(e => `${e.position}${e.company}${e.period}${e.achievements}`).join('').length
      case 'education': return educations.map(e => `${e.institution}${e.specialization}${e.degree}${e.year}`).join('').length
      case 'skills': return [...skills, ...aiSkills].join(', ').length
      case 'about': return aboutText.length
      default: return 0
    }
  }

  const charCount = getCharCount()
  const limits = CHAR_LIMITS[activeSection]
  const charStatus = charCount < limits.min ? 'short' : charCount > limits.max ? 'long' : 'good'

  const addSkill = () => {
    if (newSkill.trim() && !skills.includes(newSkill.trim())) {
      setSkills([...skills, newSkill.trim()])
      setNewSkill('')
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button onClick={() => navigate(-1)} className="btn btn-secondary btn-sm"><ArrowLeft size={16} /></button>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Редактор резюме</h2>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-secondary btn-sm" onClick={handleSave} disabled={saving}>
            {saving ? <><Loader size={14} className="spin" /> Сохранение...</> : <><Save size={14} /> Сохранить черновик</>}
          </button>
          {saveMsg && <span style={{ fontSize: '0.8rem', color: saveMsg.includes('Ошибка') ? 'var(--error)' : 'var(--success)' }}>{saveMsg}</span>}
          <button onClick={() => navigate('/app/export')} className="btn btn-primary btn-sm"><Download size={14} /> Экспорт</button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr 260px', gap: '1.5rem' }}>
        {/* Sidebar sections with icons */}
        <div className="card" style={{ padding: '0.5rem', height: 'fit-content' }}>
          {SECTIONS.map(s => {
            const Icon = s.icon
            return (
              <div
                key={s.id}
                onClick={() => setActiveSection(s.id)}
                style={{
                  padding: '0.65rem 0.85rem', borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                  fontWeight: activeSection === s.id ? 600 : 400, fontSize: '0.9rem',
                  background: activeSection === s.id ? 'var(--primary-bg)' : 'transparent',
                  color: activeSection === s.id ? 'var(--primary)' : 'var(--text-secondary)',
                  display: 'flex', alignItems: 'center', gap: '0.5rem',
                }}
              >
                <Icon size={16} />
                {s.label}
              </div>
            )
          })}
        </div>

        {/* Editor area — structured forms */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontWeight: 600, fontSize: '1rem' }}>{SECTIONS.find(s => s.id === activeSection)?.label}</h3>
            <span style={{
              fontSize: '0.8rem',
              color: charStatus === 'good' ? 'var(--success)' : charStatus === 'short' ? '#D97706' : 'var(--danger)',
            }}>
              {charStatus === 'good' ? '✓ Отлично' : charStatus === 'short' ? '⚠ Коротко' : '⚠ Длинно'} · {charCount} символов / рекомендуется {limits.min}–{limits.max}
            </span>
          </div>

          {/* Header section — structured fields */}
          {activeSection === 'header' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="input-group">
                <label className="input-label">ФИО</label>
                <input className="input-field" value={headerData.fullName} onChange={e => setHeaderData({ ...headerData, fullName: e.target.value })} />
              </div>
              <div className="input-group">
                <label className="input-label">Должность</label>
                <input className="input-field" value={headerData.position} onChange={e => setHeaderData({ ...headerData, position: e.target.value })} />
              </div>
              <div className="input-group">
                <label className="input-label">Email</label>
                <input className="input-field" type="email" value={headerData.email} onChange={e => setHeaderData({ ...headerData, email: e.target.value })} />
              </div>
              <div className="input-group">
                <label className="input-label">Телефон</label>
                <input className="input-field" value={headerData.phone} onChange={e => setHeaderData({ ...headerData, phone: e.target.value })} />
              </div>
              <div className="input-group">
                <label className="input-label">Город</label>
                <input className="input-field" value={headerData.city} onChange={e => setHeaderData({ ...headerData, city: e.target.value })} />
              </div>
              <div className="input-group">
                <label className="input-label">LinkedIn / Telegram</label>
                <input className="input-field" value={headerData.linkedin} onChange={e => setHeaderData({ ...headerData, linkedin: e.target.value })} />
              </div>
            </div>
          )}

          {/* Experience section — structured */}
          {activeSection === 'experience' && (
            <div>
              {experiences.map((exp, idx) => (
                <div key={idx} style={{ marginBottom: '1.5rem', padding: '1rem', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                    <div className="input-group">
                      <label className="input-label">Должность</label>
                      <input className="input-field" value={exp.position} onChange={e => {
                        const u = [...experiences]; u[idx] = { ...u[idx], position: e.target.value }; setExperiences(u)
                      }} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Компания</label>
                      <input className="input-field" value={exp.company} onChange={e => {
                        const u = [...experiences]; u[idx] = { ...u[idx], company: e.target.value }; setExperiences(u)
                      }} />
                    </div>
                  </div>
                  <div className="input-group" style={{ marginBottom: '1rem' }}>
                    <label className="input-label">Период</label>
                    <input className="input-field" value={exp.period} onChange={e => {
                      const u = [...experiences]; u[idx] = { ...u[idx], period: e.target.value }; setExperiences(u)
                    }} />
                  </div>
                  <div className="input-group">
                    <label className="input-label">Достижения (каждое с новой строки)</label>
                    <textarea className="input-field" rows={5} style={{ fontFamily: 'inherit', lineHeight: 1.7 }} value={exp.achievements} onChange={e => {
                      const u = [...experiences]; u[idx] = { ...u[idx], achievements: e.target.value }; setExperiences(u)
                    }} />
                  </div>
                </div>
              ))}
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setExperiences([...experiences, { position: '', company: '', period: '', achievements: '' }])}
              >
                <Plus size={14} /> Добавить место работы
              </button>
            </div>
          )}

          {/* Education section — structured */}
          {activeSection === 'education' && (
            <div>
              {educations.map((edu, idx) => (
                <div key={idx} style={{ marginBottom: '1.5rem', padding: '1rem', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                    <div className="input-group">
                      <label className="input-label">ВУЗ</label>
                      <input className="input-field" value={edu.institution} onChange={e => {
                        const u = [...educations]; u[idx] = { ...u[idx], institution: e.target.value }; setEducations(u)
                      }} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Специальность</label>
                      <input className="input-field" value={edu.specialization} onChange={e => {
                        const u = [...educations]; u[idx] = { ...u[idx], specialization: e.target.value }; setEducations(u)
                      }} />
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div className="input-group">
                      <label className="input-label">Степень</label>
                      <select className="input-field select-field" value={edu.degree} onChange={e => {
                        const u = [...educations]; u[idx] = { ...u[idx], degree: e.target.value }; setEducations(u)
                      }}>
                        <option>Бакалавриат</option>
                        <option>Магистратура</option>
                        <option>Специалитет</option>
                        <option>Аспирантура</option>
                      </select>
                    </div>
                    <div className="input-group">
                      <label className="input-label">Год окончания</label>
                      <input className="input-field" value={edu.year} onChange={e => {
                        const u = [...educations]; u[idx] = { ...u[idx], year: e.target.value }; setEducations(u)
                      }} />
                    </div>
                  </div>
                </div>
              ))}
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setEducations([...educations, { institution: '', specialization: '', degree: 'Бакалавриат', year: '' }])}
              >
                <Plus size={14} /> Добавить образование
              </button>
            </div>
          )}

          {/* Skills section — interactive tags */}
          {activeSection === 'skills' && (
            <div>
              <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                {skills.map(s => (
                  <span key={s} className="badge badge-indigo" style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    {s}
                    <X size={12} onClick={() => setSkills(skills.filter(sk => sk !== s))} />
                  </span>
                ))}
                {aiSkills.map(s => (
                  <span key={s} className="badge badge-green" style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }} title="Добавлено AI">
                    {s} <Sparkles size={10} />
                  </span>
                ))}
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  className="input-field"
                  placeholder="Добавить навык..."
                  value={newSkill}
                  onChange={e => setNewSkill(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addSkill())}
                  style={{ flex: 1 }}
                />
                <button className="btn btn-primary btn-sm" onClick={addSkill}>Добавить</button>
              </div>
            </div>
          )}

          {/* About section */}
          {activeSection === 'about' && (
            <textarea
              value={aboutText}
              onChange={e => setAboutText(e.target.value)}
              className="input-field"
              style={{ minHeight: 200, fontFamily: 'inherit', lineHeight: 1.7, resize: 'vertical' }}
            />
          )}
        </div>

        {/* AI Hints panel — matches prototype */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.25rem' }}>
            <Sparkles size={14} style={{ verticalAlign: '-2px', marginRight: '0.35rem' }} />
            AI-подсказки
          </div>
          {AI_HINTS.map((hint, i) => (
            <div key={i} style={{
              padding: '0.85rem', borderRadius: 'var(--radius-sm)',
              background: hint.bg, border: `1px solid ${hint.color}22`, fontSize: '0.83rem',
            }}>
              <div style={{ fontWeight: 600, marginBottom: '0.25rem', color: hint.color }}>{hint.title}</div>
              {hint.text}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
