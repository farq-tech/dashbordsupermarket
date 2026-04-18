'use client'
import { useAppStore } from '@/store/useAppStore'
import { Button } from '@/components/ui/button'
import { PanelRightOpen, PanelRightClose, RefreshCw, Globe, Menu } from 'lucide-react'
import { RetailerLogo } from '@/components/ui/RetailerLogo'

interface TopbarProps {
  title_ar: string
  title_en?: string
  subtitle_ar?: string
  subtitle_en?: string
  /** PDD §7 — short page description under title */
  description_ar?: string
  description_en?: string
}

export function Topbar({
  title_ar,
  title_en,
  subtitle_ar,
  subtitle_en,
  description_ar,
  description_en,
}: TopbarProps) {
  const { lang, setLang, refreshing, forceRefresh, lastUpdated, selectedRetailer, dataSource, setDataSource, mobileNavOpen, setMobileNavOpen, desktopSidebarHidden, setDesktopSidebarHidden } = useAppStore()

  const formatDate = (iso: string | null) => {
    if (!iso) return lang === 'ar' ? 'لم يتم التحميل بعد' : 'Not loaded yet'
    const d = new Date(iso)
    return d.toLocaleString(lang === 'ar' ? 'ar-SA' : 'en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    })
  }

  const desc = lang === 'ar' ? description_ar : description_en

  return (
    <header
      data-testid="app-topbar"
      className="min-h-20 flex flex-col justify-center gap-1 px-3 sm:px-6 py-3 sticky top-0 z-30"
      style={{
        background: 'var(--color-topbar-bg)',
        borderBottom: '1px solid var(--color-border)',
        paddingTop: 'max(0.75rem, env(safe-area-inset-top, 0px))',
      }}
    >
      <div className="flex flex-wrap items-center gap-2 sm:gap-4 w-full">
        <button
          type="button"
          className="md:hidden flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border touch-manipulation"
          style={{
            borderColor: 'var(--color-border)',
            background: 'var(--color-surface)',
            color: 'var(--color-text-primary)',
          }}
          aria-label={lang === 'ar' ? 'فتح القائمة' : 'Open menu'}
          aria-expanded={mobileNavOpen}
          onClick={() => setMobileNavOpen(true)}
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="flex-1 min-w-0 basis-[min(100%,12rem)] sm:basis-auto">
          <h1 className="text-base font-bold truncate" style={{ color: 'var(--color-text-primary)' }}>
            {lang === 'ar' ? title_ar : (title_en ?? title_ar)}
          </h1>
          {(subtitle_ar || subtitle_en) && (
            <p className="text-xs truncate mt-0.5" style={{ color: '#889DB4' }}>
              {lang === 'ar' ? subtitle_ar : subtitle_en}
            </p>
          )}
          {desc && (
            <p className="text-sm mt-2 leading-snug max-w-3xl" style={{ color: 'var(--color-text-secondary)' }}>
              {desc}
            </p>
          )}
        </div>

        {selectedRetailer && (
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg shrink-0 border" style={{ background: 'var(--color-surface-muted)', borderColor: 'var(--color-border)' }}>
            <RetailerLogo
              retailer={selectedRetailer}
              label={lang === 'ar' ? selectedRetailer.brand_ar : selectedRetailer.brand_en}
              size={20}
              rounded="md"
            />
            <span className="text-sm font-medium truncate max-w-[140px]" style={{ color: 'var(--color-text-primary)' }}>
              {lang === 'ar' ? selectedRetailer.brand_ar : selectedRetailer.brand_en}
            </span>
          </div>
        )}

        <div
          className="hidden md:flex shrink-0 items-center gap-0.5 p-1 rounded-lg border"
          style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
        >
          <button
            type="button"
            onClick={() => setDataSource('supermarket')}
            className="px-2 sm:px-3 py-1.5 text-xs sm:text-sm rounded-md transition-colors whitespace-nowrap"
            style={{
              background: dataSource === 'supermarket' ? 'var(--color-surface-muted)' : 'transparent',
              color: 'var(--color-text-primary)',
            }}
          >
            {lang === 'ar' ? 'متاجر التجزئة' : 'Retail Market'}
          </button>
          <button
            type="button"
            onClick={() => setDataSource('restaurants')}
            className="px-2 sm:px-3 py-1.5 text-xs sm:text-sm rounded-md transition-colors whitespace-nowrap"
            style={{
              background: dataSource === 'restaurants' ? 'var(--color-surface-muted)' : 'transparent',
              color: 'var(--color-text-primary)',
            }}
          >
            {lang === 'ar' ? 'تطبيقات التوصيل' : 'Delivery Apps'}
          </button>
        </div>

        <button
          type="button"
          onClick={() => setDesktopSidebarHidden(!desktopSidebarHidden)}
          className="hidden md:flex h-9 w-9 items-center justify-center rounded-lg border shrink-0"
          style={{
            borderColor: 'var(--color-border)',
            background: 'var(--color-surface)',
            color: 'var(--color-text-primary)',
          }}
          aria-label={lang === 'ar' ? 'إظهار/إخفاء الشريط الجانبي' : 'Toggle sidebar'}
          title={lang === 'ar' ? 'إظهار/إخفاء الشريط الجانبي' : 'Toggle sidebar'}
        >
          {desktopSidebarHidden ? <PanelRightOpen className="h-4 w-4" /> : <PanelRightClose className="h-4 w-4" />}
        </button>

        <span className="text-xs hidden lg:block shrink-0" style={{ color: '#889DB4' }}>
          {lang === 'ar' ? 'آخر تحديث:' : 'Last updated:'} {formatDate(lastUpdated)}
        </span>

        <Button
          variant="outline"
          size="sm"
          loading={refreshing}
          onClick={() => forceRefresh()}
          className="shrink-0 touch-manipulation min-h-[44px] sm:min-h-0"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">{lang === 'ar' ? 'تحديث البيانات' : 'Refresh'}</span>
        </Button>

        <button
          type="button"
          onClick={() => setLang(lang === 'ar' ? 'en' : 'ar')}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg border text-sm transition-colors shrink-0 touch-manipulation min-h-[44px] sm:min-h-0 sm:py-1.5"
          style={{
            borderColor: 'var(--color-border)',
            color: 'var(--color-text-primary)',
            background: 'var(--color-surface)',
          }}
          aria-label={lang === 'ar' ? 'Switch to English' : 'التبديل إلى العربية'}
        >
          <Globe className="h-3.5 w-3.5" />
          {lang === 'ar' ? 'EN' : 'عر'}
        </button>
      </div>
    </header>
  )
}
