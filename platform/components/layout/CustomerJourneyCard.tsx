'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LayoutDashboard, Stethoscope, Zap, Store } from 'lucide-react'
import { getExperience, type ExperienceMode } from '@/lib/experienceCopy'
import { cn } from '@/components/ui/cn'

const DIAGNOSIS_PREFIXES = ['/pricing', '/coverage', '/competitors', '/categories', '/products'] as const

function isDiagnosisPath(pathname: string) {
  return DIAGNOSIS_PREFIXES.some(p => pathname === p || pathname.startsWith(`${p}/`))
}

const STEP_HREFS = ['/dashboard', '/pricing', '/recommendations', '/profile'] as const
const STEP_ICONS = [LayoutDashboard, Stethoscope, Zap, Store] as const

interface CustomerJourneyCardProps {
  lang: 'ar' | 'en'
  dataSource: ExperienceMode
}

export function CustomerJourneyCard({ lang, dataSource }: CustomerJourneyCardProps) {
  const pathname = usePathname() ?? ''
  const isAr = lang === 'ar'
  const xp = getExperience(dataSource)

  return (
    <section
      className="rounded-[var(--radius-lg)] border overflow-hidden mb-[var(--density-grid-gap)]"
      style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
      aria-labelledby="journey-heading"
    >
      <div
        className="px-4 py-3 border-b flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between"
        style={{
          borderColor: 'var(--color-border)',
          background:
            dataSource === 'supermarket'
              ? 'color-mix(in srgb, var(--color-trend-up) 6%, var(--color-surface-muted))'
              : 'color-mix(in srgb, var(--color-interactive) 7%, var(--color-surface-muted))',
        }}
      >
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wide mb-0.5" style={{ color: 'var(--color-text-muted)' }}>
            {dataSource === 'supermarket'
              ? (isAr ? 'وضع السوبرماركت' : 'Supermarket mode')
              : (isAr ? 'وضع التوصيل' : 'Delivery mode')}
          </p>
          <h2 id="journey-heading" className="text-sm font-bold" style={{ color: 'var(--color-text-primary)' }}>
            {isAr ? xp.journeyHeading_ar : xp.journeyHeading_en}
          </h2>
          <p className="text-xs mt-0.5 max-w-2xl leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
            {isAr ? xp.journeyIntro_ar : xp.journeyIntro_en}
          </p>
        </div>
        <p className="text-[10px] font-medium shrink-0" style={{ color: 'var(--color-text-muted)' }}>
          {isAr ? xp.journeySub_ar : xp.journeySub_en}
        </p>
      </div>
      <div className="p-3 sm:p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-3">
        {xp.steps.map((stepCopy, i) => {
          const stepNum = i + 1
          const href = STEP_HREFS[i]
          const active =
            stepNum === 2
              ? isDiagnosisPath(pathname)
              : stepNum === 3
                ? pathname === '/recommendations' || pathname.startsWith('/recommendations/')
                  || pathname === '/decisions' || pathname.startsWith('/decisions/')
                : pathname === href || pathname.startsWith(`${href}/`)
          const Icon = STEP_ICONS[i]
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'group flex flex-col gap-2 rounded-xl border p-3 transition-all text-start',
                active ? 'ring-2' : 'hover:opacity-95',
              )}
              style={{
                borderColor: active ? 'var(--color-interactive)' : 'var(--color-border)',
                background: active ? 'color-mix(in srgb, var(--color-interactive) 8%, transparent)' : 'var(--color-surface)',
                boxShadow: active ? '0 0 0 1px color-mix(in srgb, var(--color-interactive) 35%, transparent)' : undefined,
              }}
            >
              <div className="flex items-center gap-2">
                <span
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold shrink-0"
                  style={{
                    background: active ? 'var(--color-interactive)' : 'var(--color-surface-muted)',
                    color: active ? '#fff' : 'var(--color-text-secondary)',
                  }}
                >
                  {stepNum}
                </span>
                <Icon className="h-4 w-4 shrink-0 opacity-80" style={{ color: 'var(--color-text-primary)' }} />
                <span className="text-sm font-semibold flex-1 min-w-0" style={{ color: 'var(--color-text-primary)' }}>
                  {isAr ? stepCopy.title_ar : stepCopy.title_en}
                </span>
              </div>
              <p className="text-[11px] leading-snug ps-10" style={{ color: 'var(--color-text-muted)' }}>
                {isAr ? stepCopy.desc_ar : stepCopy.desc_en}
              </p>
              <span className="text-[10px] font-medium ps-10" style={{ color: 'var(--color-interactive)' }}>
                {isAr ? 'انتقل ←' : 'Go →'}
              </span>
            </Link>
          )
        })}
      </div>
      <div
        className="px-4 py-2.5 border-t text-[11px] flex flex-wrap gap-x-4 gap-y-1"
        style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-muted)' }}
      >
        <span>{isAr ? 'روابط سريعة:' : 'Quick links:'}</span>
        <Link href="/competitors" className="underline font-medium" style={{ color: 'var(--color-interactive)' }}>
          {isAr ? xp.quick1_ar : xp.quick1_en}
        </Link>
        <Link href="/products" className="underline font-medium" style={{ color: 'var(--color-interactive)' }}>
          {isAr ? xp.quick2_ar : xp.quick2_en}
        </Link>
        <Link href="/decisions" className="underline font-medium" style={{ color: 'var(--color-interactive)' }}>
          {isAr ? xp.quick3_ar : xp.quick3_en}
        </Link>
      </div>
    </section>
  )
}
