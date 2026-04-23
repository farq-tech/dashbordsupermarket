'use client'

import { useEffect } from 'react'
import { useAppStore } from '@/store/useAppStore'

/**
 * Syncs document.documentElement lang/dir with the Zustand store lang preference.
 * Rendered once in the root layout so any language toggle propagates immediately.
 */
export function HtmlLangSync() {
  const lang = useAppStore(s => s.lang)

  useEffect(() => {
    document.documentElement.lang = lang
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
  }, [lang])

  return null
}
