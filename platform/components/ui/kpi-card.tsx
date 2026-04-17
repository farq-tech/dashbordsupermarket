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
  color = '#1a5c3a',
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
          <p className="text-xs text-neutral-500 font-medium mb-1">{title}</p>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-bold tabular-nums" style={{ color }}>
              {value}
            </span>
            {unit && <span className="text-sm text-neutral-400">{unit}</span>}
          </div>
          {subtitle && <p className="text-xs text-neutral-400 mt-1">{subtitle}</p>}
          {trend !== undefined && (
            <p className={cn(
              'text-xs mt-1.5 font-medium',
              trendPositive && 'text-green-600',
              trendNegative && 'text-red-600',
              !trendPositive && !trendNegative && 'text-neutral-400',
            )}>
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
