'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAppStore } from '@/store/useAppStore'
import { cn } from '@/components/ui/cn'
import { RetailerLogo } from '@/components/ui/RetailerLogo'
import { Bell } from 'lucide-react'
import { NAV_SECTIONS } from '@/lib/navConfig'

type Variant = 'desktop' | 'drawer'

interface SidebarPanelProps {
  /** Call after navigation / selection so mobile drawer can close */
  onInteract?: () => void
  variant?: Variant
}

export function SidebarPanel({ onInteract, variant = 'desktop' }: SidebarPanelProps) {
  const pathname = usePathname()
  const { lang, retailers, selectedRetailer, setRetailer, dashboardData, dataSource, setDataSource } = useAppStore()
  const alertsCount = dashboardData?.alerts?.length ?? 0

  const touchNav = variant === 'drawer'
  const linkPad = touchNav ? 'py-3 min-h-[48px]' : 'py-2'
  const btnPad = touchNav ? 'py-3 min-h-[48px]' : 'py-1.5'

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="px-4 py-4 md:py-5 border-b" style={{ borderColor: 'var(--color-border)' }}>
        <div className="flex items-center gap-2.5">
          <div
            className="h-10 w-10 md:h-9 md:w-9 rounded-[var(--radius-md)] flex items-center justify-center shrink-0"
            style={{ background: 'var(--color-brand)' }}
          >
            <span className="font-bold text-sm" style={{ color: 'var(--color-accent)', fontFamily: 'var(--font-brand)' }}>
              R
            </span>
          </div>
          <div className="min-w-0">
            <p className="font-bold text-sm leading-tight" style={{ color: 'var(--color-brand)', fontFamily: 'var(--font-brand)' }}>
              {lang === 'ar' ? 'ذكاء التجزئة' : 'Retail Intelligence'}
            </p>
            <p className="text-[11px] mt-0.5 font-medium truncate" style={{ color: 'var(--color-text-secondary)' }}>
              {lang === 'ar' ? 'منصة القرار' : 'Decision platform'}
            </p>
          </div>
        </div>
      </div>

      <div className="px-3 py-3 border-b" style={{ borderColor: 'var(--color-border)' }}>
        <p className="text-xs mb-2 px-0.5 font-medium" style={{ color: 'var(--color-text-secondary)' }}>
          {lang === 'ar' ? 'مصدر البيانات' : 'Data source'}
        </p>
        <div
          className="flex items-center gap-0.5 p-1 rounded-lg border w-full"
          style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
        >
          <button
            type="button"
            onClick={() => {
              setDataSource('supermarket')
              onInteract?.()
            }}
            className={cn('flex-1 px-2 text-[11px] md:text-[11px] leading-tight rounded-md transition-colors text-center touch-manipulation', btnPad)}
            style={{
              background: dataSource === 'supermarket' ? 'var(--color-surface-hover)' : 'transparent',
              color: 'var(--color-text-primary)',
            }}
          >
            {lang === 'ar' ? 'متاجر التجزئة' : 'Retail Market'}
          </button>
          <button
            type="button"
            onClick={() => {
              setDataSource('restaurants')
              onInteract?.()
            }}
            className={cn('flex-1 px-2 text-[11px] leading-tight rounded-md transition-colors text-center touch-manipulation', btnPad)}
            style={{
              background: dataSource === 'restaurants' ? 'var(--color-surface-hover)' : 'transparent',
              color: 'var(--color-text-primary)',
            }}
          >
            {lang === 'ar' ? 'تطبيقات التوصيل' : 'Delivery Apps'}
          </button>
        </div>
      </div>

      <div className="px-3 py-3 border-b max-h-[32vh] md:max-h-[38vh] overflow-y-auto" style={{ borderColor: 'var(--color-border)' }}>
        <p className="text-xs mb-2 px-1 font-medium" style={{ color: 'var(--color-text-secondary)' }}>
          {lang === 'ar' ? 'الشركة' : 'Business'}
        </p>
        <div className="space-y-1">
          {retailers.map(r => (
            <button
              key={r.store_key}
              type="button"
              onClick={() => {
                setRetailer(r)
                onInteract?.()
              }}
              className={cn(
                'w-full flex items-center gap-2.5 px-3 rounded-lg text-right transition-colors text-sm touch-manipulation',
                linkPad,
                selectedRetailer?.store_key === r.store_key
                  ? 'font-semibold'
                  : 'opacity-80 hover:opacity-100',
              )}
              style={{
                color: 'var(--color-text-primary)',
                background: selectedRetailer?.store_key === r.store_key
                  ? 'var(--color-surface-hover)'
                  : 'transparent',
              }}
            >
              <RetailerLogo
                retailer={r}
                label={lang === 'ar' ? r.brand_ar : r.brand_en}
                size={24}
              />
              <span className="truncate">{lang === 'ar' ? r.brand_ar : r.brand_en}</span>
            </button>
          ))}
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-5 overscroll-contain">
        {NAV_SECTIONS.map(section => (
          <div key={section.id}>
            <p
              className="text-[10px] font-semibold uppercase tracking-wider px-3 mb-1.5"
              style={{ color: '#889DB4' }}
            >
              {lang === 'ar' ? section.title_ar : section.title_en}
            </p>
            <div className="space-y-0.5">
              {section.items.map(item => {
                const active = pathname === item.href || pathname.startsWith(`${item.href}/`)
                const label = lang === 'ar' ? item.label_ar : item.label_en
                const Icon = item.icon
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => onInteract?.()}
                    className={cn(
                      'flex items-center gap-3 px-3 rounded-lg text-sm transition-colors touch-manipulation',
                      linkPad,
                      active ? 'font-semibold' : 'opacity-85 hover:opacity-100',
                    )}
                    style={{
                      color: 'var(--color-text-primary)',
                      background: active ? 'var(--color-surface-hover)' : 'transparent',
                    }}
                  >
                    <Icon className="h-4 w-4 shrink-0 opacity-90" />
                    <span className="leading-snug">{label}</span>
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {alertsCount > 0 && (
        <div className="px-3 pb-3">
          <div className="rounded-lg px-3 py-2.5 flex items-center gap-2 border" style={{ background: '#FFFBEB', borderColor: '#FCD34D' }}>
            <Bell className="h-4 w-4 shrink-0" style={{ color: '#B45309' }} />
            <span className="text-xs font-medium" style={{ color: '#92400E' }}>
              {alertsCount} {lang === 'ar' ? 'تنبيه' : 'alerts'}
            </span>
          </div>
        </div>
      )}

      <div
        className="px-4 pb-3 pt-1 border-t mt-auto"
        style={{ borderColor: 'var(--color-border)', paddingBottom: 'max(0.75rem, env(safe-area-inset-bottom, 0px))' }}
      >
        <p className="text-[11px]" style={{ color: '#889DB4' }}>v3.0</p>
      </div>
    </div>
  )
}
