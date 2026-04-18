'use client'

import { useLayoutEffect, useState } from 'react'
import { chartThemeFallback, getChartTheme, type ChartTheme } from '@/lib/chartTheme'

/**
 * Theme for Recharts: starts with CSS fallbacks for SSR-safe markup, then syncs from
 * `document.documentElement` once (via cached `getChartTheme()`).
 */
export function useChartTheme(): ChartTheme {
  const [theme, setTheme] = useState<ChartTheme>(chartThemeFallback)
  useLayoutEffect(() => {
    setTheme(getChartTheme())
  }, [])
  return theme
}
