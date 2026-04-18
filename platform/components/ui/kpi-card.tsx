import { cn } from './cn'
import { Card } from './card'

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
}: KpiCardProps) {
  const title = lang === 'ar' ? title_ar : title_en
  const trendPositive = trend !== undefined && trend > 0
  const trendNegative = trend !== undefined && trend < 0

  return (
    <Card className="card-hover">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p
            className="text-xs font-medium mb-1"
            style={{ color: 'var(--color-text-muted)' }}
          >
            {title}
          </p>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-bold tabular-nums tracking-tight" style={{ color }}>
              {value}
            </span>
            {unit && (
              <span className="text-sm" style={{ color: 'var(--color-text-subtle)' }}>
                {unit}
              </span>
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
              {trendPositive ? '▲' : trendNegative ? '▼' : '→'} {Math.abs(trend).toFixed(1)}%
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
