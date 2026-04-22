'use client'

import { AlertTriangle, RefreshCw } from 'lucide-react'
import { cn } from './cn'
import { Button } from './button'

interface ErrorStateProps {
  title_ar?: string
  title_en?: string
  description_ar?: string
  description_en?: string
  onRetry?: () => void
  lang?: 'ar' | 'en'
  className?: string
}

export function ErrorState({
  title_ar = 'حدث خطأ في تحميل البيانات',
  title_en = 'Failed to load data',
  description_ar = 'تعذّر الاتصال بالخادم. يرجى المحاولة مجدداً.',
  description_en = 'Could not reach the server. Please try again.',
  onRetry,
  lang = 'ar',
  className,
}: ErrorStateProps) {
  const isAr = lang === 'ar'
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-[var(--radius-lg)] border border-dashed border-red-200 bg-red-50/50 px-6 py-12 text-center',
        className,
      )}
    >
      <AlertTriangle className="h-10 w-10 mb-3 text-red-400" />
      <p className="text-sm font-semibold text-red-700">{isAr ? title_ar : title_en}</p>
      <p className="mt-1 max-w-sm text-xs leading-relaxed text-red-500">
        {isAr ? description_ar : description_en}
      </p>
      {onRetry && (
        <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}>
          <RefreshCw className="h-3.5 w-3.5" />
          {isAr ? 'حاول مجدداً' : 'Try again'}
        </Button>
      )}
    </div>
  )
}
