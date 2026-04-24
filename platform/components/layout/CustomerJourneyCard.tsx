'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LayoutDashboard, Stethoscope, Zap, Store } from 'lucide-react'
import type { BusinessPersona } from '@/lib/businessPersona'
import { personaJourneyIntro } from '@/lib/businessPersona'
import { cn } from '@/components/ui/cn'

const DIAGNOSIS_PREFIXES = ['/pricing', '/coverage', '/competitors', '/categories', '/products'] as const

function isDiagnosisPath(pathname: string) {
  return DIAGNOSIS_PREFIXES.some(p => pathname === p || pathname.startsWith(`${p}/`))
}

const STEPS = [
  {
    href: '/dashboard',
    step: 1,
    icon: LayoutDashboard,
    title_ar: 'نظرة عامة',
    title_en: 'Overview',
    desc_ar: 'مؤشراتك الرئيسية وترتيبك في السوق',
    desc_en: 'Key KPIs and your market rank',
  },
  {
    href: '/pricing',
    step: 2,
    icon: Stethoscope,
    title_ar: 'التشخيص',
    title_en: 'Diagnose',
    desc_ar: 'ابدأ بالتسعير، ثم المنافسين والمنتجات',
    desc_en: 'Start with pricing, then competitors & SKUs',
  },
  {
    href: '/recommendations',
    step: 3,
    icon: Zap,
    title_ar: 'التنفيذ',
    title_en: 'Execute',
    desc_ar: 'التوصيات والقرارات حسب الأولوية',
    desc_en: 'Prioritized recommendations & decisions',
  },
  {
    href: '/profile',
    step: 4,
    icon: Store,
    title_ar: 'السياق',
    title_en: 'Context',
    desc_ar: 'ملف العلامة ومصدر البيانات',
    desc_en: 'Brand profile & data source',
  },
] as const

interface CustomerJourneyCardProps {
  lang: 'ar' | 'en'
  persona: BusinessPersona
}

export function CustomerJourneyCard({ lang, persona }: CustomerJourneyCardProps) {
  const pathname = usePathname() ?? ''
  const isAr = lang === 'ar'

  return (
    <section
      className="rounded-[var(--radius-lg)] border overflow-hidden mb-[var(--density-grid-gap)]"
      style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
      aria-labelledby="journey-heading"
    >
      <div
        className="px-4 py-3 border-b flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between"
        style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface-muted)' }}
      >
        <div>
          <h2 id="journey-heading" className="text-sm font-bold" style={{ color: 'var(--color-text-primary)' }}>
            {isAr ? 'مسار العمل الموصى به' : 'Recommended workflow'}
          </h2>
          <p className="text-xs mt-0.5 max-w-2xl leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
            {personaJourneyIntro(persona, isAr)}
          </p>
        </div>
        <p className="text-[10px] font-medium shrink-0" style={{ color: 'var(--color-text-muted)' }}>
          {isAr ? '٤ خطوات — من المراقبة إلى التنفيذ' : '4 steps — monitor to execute'}
        </p>
      </div>
      <div className="p-3 sm:p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-3">
        {STEPS.map(s => {
          const active =
            s.step === 2
              ? isDiagnosisPath(pathname)
              : s.step === 3
                ? pathname === '/recommendations' || pathname.startsWith('/recommendations/')
                  || pathname === '/decisions' || pathname.startsWith('/decisions/')
                : pathname === s.href || pathname.startsWith(`${s.href}/`)
          const Icon = s.icon
          return (
            <Link
              key={s.href}
              href={s.href}
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
                  {s.step}
                </span>
                <Icon className="h-4 w-4 shrink-0 opacity-80" style={{ color: 'var(--color-text-primary)' }} />
                <span className="text-sm font-semibold flex-1 min-w-0" style={{ color: 'var(--color-text-primary)' }}>
                  {isAr ? s.title_ar : s.title_en}
                </span>
              </div>
              <p className="text-[11px] leading-snug ps-10" style={{ color: 'var(--color-text-muted)' }}>
                {isAr ? s.desc_ar : s.desc_en}
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
          {isAr ? 'مقارنة مباشرة مع منافس' : 'Head-to-head competitor'}
        </Link>
        <Link href="/products" className="underline font-medium" style={{ color: 'var(--color-interactive)' }}>
          {isAr ? 'جدول المنتجات' : 'Product table'}
        </Link>
        <Link href="/decisions" className="underline font-medium" style={{ color: 'var(--color-interactive)' }}>
          {isAr ? 'مركز القرار' : 'Decision hub'}
        </Link>
      </div>
    </section>
  )
}
