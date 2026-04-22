'use client'

import * as Tooltip from '@radix-ui/react-tooltip'
import { Info } from 'lucide-react'
import { cn } from './cn'
import { Card } from './card'
import { CountUp } from './count-up'

interface KpiCardProps {
  title_ar: string
  title_en: string
  value: string | number
  unit?: string
  subtitle?: string
  trend?: number
  color?: string
  icon?: React.ReactNode
  lang?: 'ar' | 'en'
  /** Deep-link target: `/dashboard?kpi=performance` */
  kpiId?: string
  focused?: boolean
  /** Animate main value from 0 (large KPIs only) */
  countUp?: boolean
  countDecimals?: number
  /** Optional info tooltip explaining how this KPI is calculated */
  tooltip_ar?: string
  tooltip_en?: string
}

export function KpiCard({
  title_ar,
  title_en,
  value,
  unit,
  subtitle,
  trend,
  color = '#000000',
  icon,
  lang = 'ar',
  kpiId,
  focused,
  countUp,
  countDecimals = 0,
  tooltip_ar,
  tooltip_en,
}: KpiCardProps) {
  const title = lang === 'ar' ? title_ar : title_en
  const tooltipText = lang === 'ar' ? tooltip_ar : tooltip_en
  const trendPositive = trend !== undefined && trend > 0
  const trendNegative = trend !== undefined && trend < 0

  const numericEnd =
    typeof value === 'number' ? value : Number.parseFloat(String(value).replace(/[^\d.-]/g, ''))
  const canCountUp = Boolean(countUp && Number.isFinite(numericEnd))

  return (
    <Card
      id={kpiId ? `kpi-${kpiId}` : undefined}
      className={cn(
        'card-hover scroll-mt-28',
        focused &&
          'ring-2 ring-[color:var(--color-interactive)] ring-offset-2 ring-offset-[var(--color-surface)]',
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-1 mb-[var(--density-kpi-title-mb)]">
            <p
              className="text-xs font-medium"
              style={{ color: 'var(--color-text-muted)' }}
            >
              {title}
            </p>
            {tooltipText && (
              <Tooltip.Provider delayDuration={300}>
                <Tooltip.Root>
                  <Tooltip.Trigger asChild>
                    <button
                      type="button"
                      className="shrink-0 opacity-40 hover:opacity-80 transition-opacity"
                      aria-label={lang === 'ar' ? 'مزيد من المعلومات' : 'More info'}
                    >
                      <Info className="h-3 w-3" style={{ color: 'var(--color-text-muted)' }} />
                    </button>
                  </Tooltip.Trigger>
                  <Tooltip.Portal>
                    <Tooltip.Content
                      side="top"
                      align="start"
                      sideOffset={4}
                      className="z-50 max-w-[220px] rounded-lg border px-3 py-2 text-xs leading-relaxed shadow-lg animate-fade-in"
                      style={{
                        background: 'var(--color-surface)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-text-secondary)',
                      }}
                      dir={lang === 'ar' ? 'rtl' : 'ltr'}
                    >
                      {tooltipText}
                      <Tooltip.Arrow style={{ fill: 'var(--color-border)' }} />
                    </Tooltip.Content>
                  </Tooltip.Portal>
                </Tooltip.Root>
              </Tooltip.Provider>
            )}
          </div>
          <div className="flex items-baseline gap-1.5">
            {canCountUp ? (
              <>
                <CountUp
                  end={numericEnd}
                  decimals={countDecimals}
                  className="text-2xl font-bold tabular-nums tracking-tight"
                  style={{ color }}
                />
                {unit && (
                  <span className="text-sm" style={{ color: 'var(--color-text-subtle)' }}>
                    {unit}
                  </span>
                )}
              </>
            ) : (
              <>
                <span className="text-2xl font-bold tabular-nums tracking-tight" style={{ color }}>
                  {value}
                </span>
                {unit && (
                  <span className="text-sm" style={{ color: 'var(--color-text-subtle)' }}>
                    {unit}
                  </span>
                )}
              </>
            )}
          </div>
          {subtitle && (
            <p className="text-xs mt-1" style={{ color: 'var(--color-text-subtle)' }}>
              {subtitle}
            </p>
          )}
          {trend !== undefined && (
            <p
              className={cn('text-xs mt-1.5 font-semibold')}
              style={{
                color: trendPositive
                  ? 'var(--color-trend-up)'
                  : trendNegative
                    ? 'var(--color-trend-down)'
                    : 'var(--color-text-subtle)',
              }}
            >
              {trendPositive ? '\u25b2' : trendNegative ? '\u25bc' : '\u2192'} {Math.abs(trend).toFixed(1)}%
            </p>
          )}
        </div>
        {icon && (
          <div
            className="h-10 w-10 rounded-xl flex items-center justify-center shrink-0"
            style={{ backgroundColor: `${color}15` }}
          >
            <span style={{ color }}>{icon}</span>
          </div>
        )}
      </div>
    </Card>
  )
}
