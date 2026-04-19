'use client'

import { useState } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAppStore } from '@/store/useAppStore'
import { cn } from '@/components/ui/cn'
import { RetailerLogo } from '@/components/ui/RetailerLogo'
import { Bell, ChevronDown } from 'lucide-react'
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
  const [businessOpen, setBusinessOpen] = useState(true)

  const touchNav = variant === 'drawer'
  const linkPad = touchNav ? 'py-3 min-h-[48px]' : 'py-2'
  const btnPad = touchNav ? 'py-3 min-h-[48px]' : 'py-1.5'

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="border-b px-3 py-5 sm:px-4 md:py-6" style={{ borderColor: 'var(--color-border)' }}>
        <div className="flex flex-col items-center gap-3 sm:flex-row sm:items-center sm:gap-3.5">
          <span className="relative h-[4.5rem] w-[4.5rem] shrink-0 overflow-hidden rounded-[var(--radius-lg)] bg-white shadow-[var(--shadow-tile-nested)] ring-1 ring-black/[0.07] sm:h-[5rem] sm:w-[5rem]">
            <Image
              src="/brand/farq.png"
              alt={lang === 'ar' ? 'فرق' : 'Farq'}
              fill
              className="object-contain p-2.5 sm:p-3"
              sizes="96px"
              priority
            />
          </span>
          <div className="min-w-0 w-full text-center sm:flex-1 sm:text-start">
            <p
              className="text-base font-bold leading-snug sm:text-[1.05rem]"
              style={{ color: 'var(--color-brand)', fontFamily: 'var(--font-brand)' }}
            >
              {lang === 'ar' ? 'ذكاء التجزئة' : 'Retail Intelligence'}
            </p>
            <p className="mt-1 text-xs font-medium leading-snug sm:text-sm" style={{ color: 'var(--color-text-secondary)' }}>
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
              background: dataSource === 'supermarket' ? 'var(--color-surface-muted)' : 'transparent',
              color:
                dataSource === 'supermarket' ? 'var(--color-interactive)' : 'var(--color-text-primary)',
              fontWeight: dataSource === 'supermarket' ? 600 : 500,
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
              background: dataSource === 'restaurants' ? 'var(--color-surface-muted)' : 'transparent',
              color:
                dataSource === 'restaurants' ? 'var(--color-interactive)' : 'var(--color-text-primary)',
              fontWeight: dataSource === 'restaurants' ? 600 : 500,
            }}
          >
            {lang === 'ar' ? 'تطبيقات التوصيل' : 'Delivery Apps'}
          </button>
        </div>
      </div>

      <div className="border-b px-3 py-3" style={{ borderColor: 'var(--color-border)' }}>
        <button
          type="button"
          className="mb-2 flex w-full items-center justify-between gap-2 rounded-lg px-1 py-0.5 text-start hover:bg-[var(--color-surface-muted)]/80"
          onClick={() => setBusinessOpen(o => !o)}
          aria-expanded={businessOpen}
          aria-controls="sidebar-business-list"
          id="sidebar-business-heading"
        >
          <span className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>
            {lang === 'ar' ? 'الشركة' : 'Business'}
          </span>
          <ChevronDown
            className={cn('h-4 w-4 shrink-0 opacity-70 transition-transform duration-200', !businessOpen && '-rotate-90')}
            aria-hidden
          />
        </button>
        {businessOpen && (
          <div
            id="sidebar-business-list"
            role="region"
            aria-labelledby="sidebar-business-heading"
            className="max-h-[32vh] space-y-1 overflow-y-auto md:max-h-[38vh]"
          >
            {retailers.map(r => (
              <button
                key={r.store_key}
                type="button"
                onClick={() => {
                  setRetailer(r)
                  onInteract?.()
                }}
                className={cn(
                  'flex w-full items-center gap-3 rounded-lg px-3 text-start transition-colors text-sm touch-manipulation',
                  linkPad,
                  selectedRetailer?.store_key === r.store_key
                    ? 'font-semibold'
                    : 'opacity-80 hover:opacity-100',
                )}
                style={{
                  color:
                    selectedRetailer?.store_key === r.store_key
                      ? 'var(--color-interactive)'
                      : 'var(--color-text-primary)',
                  background:
                    selectedRetailer?.store_key === r.store_key
                      ? 'var(--color-surface-hover)'
                      : 'transparent',
                }}
              >
                <RetailerLogo
                  retailer={r}
                  label={lang === 'ar' ? r.brand_ar : r.brand_en}
                  size={44}
                  rounded="lg"
                />
                <span className="truncate">{lang === 'ar' ? r.brand_ar : r.brand_en}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-5 overscroll-contain">
        {NAV_SECTIONS.map(section => (
          <div key={section.id}>
            <p
              className="text-[10px] font-semibold uppercase tracking-wider px-3 mb-1.5"
              style={{ color: 'var(--color-text-muted)' }}
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
                      color: active ? 'var(--color-interactive)' : 'var(--color-text-primary)',
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
        <p className="text-[11px]" style={{ color: 'var(--color-text-subtle)' }}>v3.0</p>
      </div>
    </div>
  )
}
