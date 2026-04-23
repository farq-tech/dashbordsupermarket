'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'

export default function RouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('[route-error]', error)
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 p-6 text-center animate-fade-in">
      <div
        className="h-14 w-14 rounded-2xl flex items-center justify-center text-2xl"
        style={{ background: 'var(--color-surface-muted)' }}
      >
        ⚠️
      </div>
      <div>
        <h2 className="text-base font-bold" style={{ color: 'var(--color-text-primary)' }}>
          حدث خطأ غير متوقع
        </h2>
        <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
          An unexpected error occurred in this section.
        </p>
        {error.digest && (
          <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
            Error ID: {error.digest}
          </p>
        )}
      </div>
      <div className="flex gap-2">
        <Button variant="primary" size="sm" onClick={reset}>
          إعادة المحاولة / Retry
        </Button>
        <Button variant="outline" size="sm" onClick={() => { window.location.href = '/dashboard' }}>
          الرئيسية / Home
        </Button>
      </div>
    </div>
  )
}
