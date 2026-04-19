'use client'

import { useSyncExternalStore } from 'react'
import { chartThemeFallback, getChartTheme, type ChartTheme } from '@/lib/chartTheme'

/**
 * Theme for Recharts: SSR uses CSS fallbacks; client reads cached `getChartTheme()` from
 * `document.documentElement`.
 */
export function useChartTheme(): ChartTheme {
  return useSyncExternalStore(
    () => () => {},
    getChartTheme,
    (): ChartTheme => chartThemeFallback,
  )
}
