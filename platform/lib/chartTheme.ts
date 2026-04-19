import type { CSSProperties } from 'react'

export type ChartTheme = {
  interactive: string
  chartLine: string
  trendUp: string
  trendDown: string
  grid: string
  axisTick: string
  axisLabel: string
  border: string
  shadow: string
  scatterTags: Record<
    'overpriced' | 'underpriced' | 'competitive' | 'opportunity' | 'risk' | 'not_stocked',
    string
  >
}

/** Mirrors `app/globals.css` @theme (Fareeq tokens) — SSR / pre-paint fallback. */
export const chartThemeFallback: ChartTheme = {
  interactive: '#22577a',
  chartLine: '#22577a',
  trendUp: '#16a34a',
  trendDown: '#ef8354',
  grid: '#dde5e8',
  axisTick: '#6b7f82',
  axisLabel: 'rgba(6, 59, 55, 0.42)',
  border: '#dbe8ee',
  shadow: '0 5px 20px rgba(4, 52, 52, 0.06)',
  scatterTags: {
    overpriced: '#ef8354',
    underpriced: '#16a34a',
    competitive: '#22577a',
    opportunity: '#ca8a04',
    risk: '#ea580c',
    not_stocked: '#94a3b8',
  },
}

function readVar(root: HTMLElement, name: string, fallback: string): string {
  const v = getComputedStyle(root).getPropertyValue(name).trim()
  if (!v) return fallback
  return v
}

export function resolveChartTheme(root: HTMLElement): ChartTheme {
  const fb = chartThemeFallback
  return {
    interactive: readVar(root, '--color-interactive', fb.interactive),
    chartLine: readVar(root, '--color-chart-line', fb.chartLine),
    trendUp: readVar(root, '--color-trend-up', fb.trendUp),
    trendDown: readVar(root, '--color-trend-down', fb.trendDown),
    grid: readVar(root, '--color-grid', fb.grid),
    axisTick: readVar(root, '--color-axis-tick', fb.axisTick),
    axisLabel: readVar(root, '--color-text-subtle', fb.axisLabel),
    border: readVar(root, '--color-border', fb.border),
    shadow: readVar(root, '--shadow-tile', fb.shadow),
    scatterTags: {
      overpriced: readVar(root, '--color-trend-down', fb.scatterTags.overpriced),
      underpriced: readVar(root, '--color-trend-up', fb.scatterTags.underpriced),
      competitive: readVar(root, '--color-interactive', fb.scatterTags.competitive),
      opportunity: readVar(root, '--color-chart-tag-opportunity', fb.scatterTags.opportunity),
      risk: readVar(root, '--color-chart-tag-risk', fb.scatterTags.risk),
      not_stocked: readVar(root, '--color-chart-tag-muted', fb.scatterTags.not_stocked),
    },
  }
}

let clientResolved: ChartTheme | null = null

/** Resolves CSS variables once per full page load (client only). */
export function getChartTheme(): ChartTheme {
  if (typeof document === 'undefined') return chartThemeFallback
  if (!clientResolved) clientResolved = resolveChartTheme(document.documentElement)
  return clientResolved
}

export function chartTooltipStyle(theme: ChartTheme, extra?: Partial<CSSProperties>): CSSProperties {
  return {
    borderRadius: 12,
    border: `1px solid ${theme.border}`,
    fontSize: 12,
    boxShadow: theme.shadow,
    ...extra,
  }
}
