'use client'
import { useAppStore } from '@/store/useAppStore'
import { Button } from '@/components/ui/button'
import { RefreshCw, Globe } from 'lucide-react'

interface TopbarProps {
  title_ar: string
  title_en?: string
  subtitle_ar?: string
  subtitle_en?: string
}

export function Topbar({ title_ar, title_en, subtitle_ar, subtitle_en }: TopbarProps) {
  const { lang, setLang, refreshing, forceRefresh, lastUpdated, selectedRetailer } = useAppStore()

  const formatDate = (iso: string | null) => {
    if (!iso) return lang === 'ar' ? 'لم يتم التحميل بعد' : 'Not loaded yet'
    const d = new Date(iso)
    return d.toLocaleString(lang === 'ar' ? 'ar-SA' : 'en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    })
  }

  return (
    <header
      className="h-20 flex items-center px-6 gap-4 sticky top-0 z-30"
      style={{
        background: 'var(--color-topbar-bg)',
        borderBottom: '1px solid var(--color-border)',
      }}
    >
      {/* Title */}
      <div className="flex-1 min-w-0">
        <h1 className="text-base font-bold truncate" style={{ color: 'var(--color-text-primary)' }}>
          {lang === 'ar' ? title_ar : (title_en ?? title_ar)}
        </h1>
        {(subtitle_ar || subtitle_en) && (
          <p className="text-xs truncate" style={{ color: '#889DB4' }}>
            {lang === 'ar' ? subtitle_ar : subtitle_en}
          </p>
        )}
      </div>

      {/* Retailer indicator */}
      {selectedRetailer && (
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{ background: 'var(--color-surface-muted)' }}>
          <span
            className="h-5 w-5 rounded flex items-center justify-center text-xs font-bold text-white"
            style={{ backgroundColor: selectedRetailer.color }}
          >
            {selectedRetailer.logo_letter}
          </span>
          <span className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>
            {lang === 'ar' ? selectedRetailer.brand_ar : selectedRetailer.brand_en}
          </span>
        </div>
      )}

      {/* Last updated */}
      <span className="text-xs hidden md:block" style={{ color: '#889DB4' }}>
        {lang === 'ar' ? 'آخر تحديث:' : 'Last update:'} {formatDate(lastUpdated)}
      </span>

      {/* Refresh button */}
      <Button
        variant="outline"
        size="sm"
        loading={refreshing}
        onClick={() => forceRefresh()}
      >
        <RefreshCw className="h-3.5 w-3.5" />
        {lang === 'ar' ? 'تحديث' : 'Refresh'}
      </Button>

      {/* Language toggle */}
      <button
        onClick={() => setLang(lang === 'ar' ? 'en' : 'ar')}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-sm transition-colors"
        style={{
          borderColor: 'var(--color-border)',
          color: 'var(--color-text-primary)',
          background: 'var(--color-surface)',
        }}
      >
        <Globe className="h-3.5 w-3.5" />
        {lang === 'ar' ? 'EN' : 'عر'}
      </button>
    </header>
  )
}
