import { cn } from './cn'
import { Lightbulb, AlertTriangle, Sparkles } from 'lucide-react'

type InsightTone = 'neutral' | 'attention' | 'positive'

const toneStyles: Record<InsightTone, { border: string; bg: string; icon: typeof Lightbulb; iconColor: string }> = {
  neutral: {
    border: 'var(--color-border)',
    bg: 'var(--color-surface-muted)',
    icon: Lightbulb,
    iconColor: 'var(--color-interactive)',
  },
  attention: {
    border: '#FCD34D',
    bg: '#FFFBEB',
    icon: AlertTriangle,
    iconColor: '#B45309',
  },
  positive: {
    border: 'rgba(27, 89, 248, 0.22)',
    bg: 'var(--color-surface-muted)',
    icon: Sparkles,
    iconColor: 'var(--color-interactive)',
  },
}

interface InsightCardProps {
  title_ar: string
  title_en: string
  body_ar: string
  body_en: string
  lang: 'ar' | 'en'
  tone?: InsightTone
  className?: string
}

/** PDD §7 — Insight summary: what is happening, why it matters, what to do */
export function InsightCard({
  title_ar,
  title_en,
  body_ar,
  body_en,
  lang,
  tone = 'neutral',
  className,
}: InsightCardProps) {
  const t = toneStyles[tone]
  const Icon = t.icon
  const title = lang === 'ar' ? title_ar : title_en
  const body = lang === 'ar' ? body_ar : body_en

  return (
    <div
      className={cn('rounded-[var(--radius-lg)] border p-4 md:p-5', className)}
      style={{ borderColor: t.border, background: t.bg }}
    >
      <div className="flex gap-3">
        <Icon className="h-5 w-5 shrink-0 mt-0.5" style={{ color: t.iconColor }} aria-hidden />
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>
            {lang === 'ar' ? 'ملخص الرؤى' : 'Insight summary'}
          </p>
          <h2 className="text-sm md:text-base font-bold leading-snug" style={{ color: 'var(--color-text-primary)' }}>
            {title}
          </h2>
          <p className="text-sm mt-2 leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
            {body}
          </p>
        </div>
      </div>
    </div>
  )
}
