'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAppStore } from '@/store/useAppStore'
import { cn } from '@/components/ui/cn'
import {
  LayoutDashboard, Store, BarChart2, DollarSign, Map, Users, Tag, Lightbulb, Bell
} from 'lucide-react'

const NAV_ITEMS = [
  { href: '/dashboard', icon: LayoutDashboard, label_ar: 'نظرة عامة', label_en: 'Overview' },
  { href: '/profile', icon: Store, label_ar: 'بيانات السلسلة', label_en: 'Chain Profile' },
  { href: '/products', icon: BarChart2, label_ar: 'المنتجات', label_en: 'Products' },
  { href: '/pricing', icon: DollarSign, label_ar: 'التسعير', label_en: 'Pricing' },
  { href: '/coverage', icon: Map, label_ar: 'التغطية', label_en: 'Coverage' },
  { href: '/competitors', icon: Users, label_ar: 'المنافسون', label_en: 'Competitors' },
  { href: '/categories', icon: Tag, label_ar: 'الأقسام', label_en: 'Categories' },
  { href: '/recommendations', icon: Lightbulb, label_ar: 'الإجراءات المقترحة', label_en: 'Recommended Actions' },
]

export function Sidebar() {
  const pathname = usePathname()
  const { lang, retailers, selectedRetailer, setRetailer, dashboardData } = useAppStore()
  const alertsCount = dashboardData?.alerts?.length ?? 0

  return (
    <aside
      className="fixed top-0 right-0 h-screen w-60 flex flex-col z-40"
      style={{
        background: 'var(--color-sidebar-bg)',
        borderLeft: '1px solid var(--color-border)',
      }}
    >
      {/* Logo */}
      <div className="px-4 py-5 border-b" style={{ borderColor: 'var(--color-border)' }}>
        <div className="flex items-center gap-2.5">
          <div
            className="h-8 w-8 rounded-md flex items-center justify-center"
            style={{ background: 'var(--color-brand)' }}
          >
            <span className="font-bold text-sm" style={{ color: 'var(--color-accent)', fontFamily: 'var(--font-brand)' }}>
              S
            </span>
          </div>
          <div>
            <p className="font-bold text-sm leading-tight" style={{ color: 'var(--color-brand)', fontFamily: 'var(--font-brand)' }}>
              Supermarket
            </p>
            <p className="text-xs" style={{ color: 'var(--color-brand)', fontFamily: 'var(--font-brand)' }}>
              Intelligence
            </p>
          </div>
        </div>
      </div>

      {/* Retailer Selector */}
      <div className="px-3 py-3 border-b" style={{ borderColor: 'var(--color-border)' }}>
        <p className="text-xs mb-2 px-1" style={{ color: 'var(--color-text-secondary)' }}>
          {lang === 'ar' ? 'السلسلة' : 'Chain'}
        </p>
        <div className="space-y-1">
          {retailers.map(r => (
            <button
              key={r.store_key}
              onClick={() => setRetailer(r)}
              className={cn(
                'w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-right transition-colors text-sm',
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
              <span
                className="h-6 w-6 rounded-md flex items-center justify-center text-xs font-bold text-white shrink-0"
                style={{ backgroundColor: r.color }}
              >
                {r.logo_letter}
              </span>
              <span className="truncate">{lang === 'ar' ? r.brand_ar : r.brand_en}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-3">
        <div className="space-y-0.5">
          {NAV_ITEMS.map(item => {
            const active = pathname === item.href || pathname.startsWith(item.href + '/')
            const label = lang === 'ar' ? item.label_ar : item.label_en
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
                  active ? 'font-semibold' : 'opacity-80 hover:opacity-100',
                )}
                style={{
                  color: 'var(--color-text-primary)',
                  background: active ? 'var(--color-surface-hover)' : 'transparent',
                }}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{label}</span>
              </Link>
            )
          })}
        </div>
      </nav>

      {/* Bottom: Alerts */}
      {alertsCount > 0 && (
        <div className="px-3 pb-3">
          <div className="rounded-lg px-3 py-2 flex items-center gap-2" style={{ background: '#FEF3C7' }}>
            <Bell className="h-4 w-4 shrink-0" style={{ color: '#B45309' }} />
            <span className="text-xs" style={{ color: '#92400E' }}>
              {alertsCount} {lang === 'ar' ? 'تنبيه نشط' : 'active alerts'}
            </span>
          </div>
        </div>
      )}

      {/* Version */}
      <div className="px-4 pb-3 pt-1 border-t" style={{ borderColor: 'var(--color-border)' }}>
        <p className="text-xs" style={{ color: '#889DB4' }}>v1.0 · Beta</p>
      </div>
    </aside>
  )
}
