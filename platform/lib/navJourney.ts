import type { NavSectionId } from '@/lib/navConfig'

/** Maps URL path to the 4-step decision flow shown in the UI. */
export type JourneyPhaseId = NavSectionId | 'unknown'

const ROUTE_TO_PHASE: { prefix: string; phase: NavSectionId }[] = [
  { prefix: '/dashboard', phase: 'overview' },
  { prefix: '/pricing', phase: 'diagnosis' },
  { prefix: '/coverage', phase: 'diagnosis' },
  { prefix: '/competitors', phase: 'diagnosis' },
  { prefix: '/categories', phase: 'diagnosis' },
  { prefix: '/products', phase: 'diagnosis' },
  { prefix: '/recommendations', phase: 'action' },
  { prefix: '/decisions', phase: 'action' },
  { prefix: '/profile', phase: 'context' },
]

const PHASE_ORDER: Record<NavSectionId, number> = {
  overview: 1,
  diagnosis: 2,
  action: 3,
  context: 4,
}

const PHASE_LABELS: Record<NavSectionId, { ar: string; en: string }> = {
  overview: { ar: 'المراقبة', en: 'Monitor' },
  diagnosis: { ar: 'التشخيص', en: 'Diagnose' },
  action: { ar: 'الإجراء', en: 'Act' },
  context: { ar: 'السياق', en: 'Context' },
}

export interface JourneyMeta {
  step: number
  totalSteps: number
  phaseId: JourneyPhaseId
  label_ar: string
  label_en: string
}

export function getJourneyMetaForPath(pathname: string | null): JourneyMeta | null {
  if (!pathname) return null
  const base = pathname.split('?')[0] ?? ''
  if (base.startsWith('/dev')) return null

  let phase: NavSectionId | 'unknown' = 'unknown'
  for (const { prefix, phase: p } of ROUTE_TO_PHASE) {
    if (base === prefix || base.startsWith(`${prefix}/`)) {
      phase = p
      break
    }
  }
  if (phase === 'unknown') return null

  const step = PHASE_ORDER[phase]
  const { ar, en } = PHASE_LABELS[phase]
  return {
    step,
    totalSteps: 4,
    phaseId: phase,
    label_ar: ar,
    label_en: en,
  }
}
