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

/** Mirrors `app/globals.css` @theme — SSR / pre-paint fallback; DOM wins on client after `getChartTheme()`. */
export const chartThemeFallback: ChartTheme = {
  interactive: '#1b59f8',
  chartLine: '#1b59f8',
  trendUp: '#1fe08f',
  trendDown: '#ff3e13',
  grid: '#e4e5e7',
  axisTick: '#838383',
  axisLabel: '#9098a3',
  border: '#eff0f6',
  shadow: '0 5px 20px rgba(0, 0, 0, 0.05)',
  scatterTags: {
    overpriced: '#ff3e13',
    underpriced: '#1fe08f',
    competitive: '#1b59f8',
    opportunity: '#ca8a04',
    risk: '#ea580c',
    not_stocked: '#9ca3af',
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
