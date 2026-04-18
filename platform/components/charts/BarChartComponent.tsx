'use client'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
  ComposedChart,
  Line,
} from 'recharts'
import { chartTooltipStyle } from '@/lib/chartTheme'
import { useChartTheme } from '@/lib/useChartTheme'

interface BarChartProps {
  data: Record<string, unknown>[]
  dataKey: string
  nameKey?: string
  color?: string
  height?: number
  showGrid?: boolean
  unit?: string
  colors?: string[]
}

export function SimpleBarChart({
  data, dataKey, nameKey = 'name', color,
  height = 240, showGrid = true, unit = '', colors,
}: BarChartProps) {
  const theme = useChartTheme()
  const barColor = color ?? theme.interactive
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={theme.grid} vertical={false} />}
        <XAxis
          dataKey={nameKey}
          tick={{ fontSize: 11, fill: theme.axisTick }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: theme.axisTick }}
          axisLine={false}
          tickLine={false}
          tickFormatter={v => `${v}${unit}`}
        />
        <Tooltip
          contentStyle={chartTooltipStyle(theme)}
          formatter={(v: unknown) => [`${v}${unit}`, '']}
        />
        <Bar dataKey={dataKey} radius={[6, 6, 0, 0]} maxBarSize={48}>
          {colors
            ? data.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)
            : <Cell fill={barColor} />
          }
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

interface MultiBarProps {
  data: Record<string, unknown>[]
  keys: { dataKey: string; name: string; color: string }[]
  nameKey?: string
  height?: number
}

export function MultiBarChart({ data, keys, nameKey = 'name', height = 280 }: MultiBarProps) {
  const theme = useChartTheme()
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={theme.grid} vertical={false} />
        <XAxis dataKey={nameKey} tick={{ fontSize: 11, fill: theme.axisTick }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 11, fill: theme.axisTick }} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={chartTooltipStyle(theme)} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {keys.map(k => (
          <Bar key={k.dataKey} dataKey={k.dataKey} name={k.name} fill={k.color} radius={[6, 6, 0, 0]} maxBarSize={40} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}

interface CategoryComboProps {
  data: Record<string, unknown>[]
  nameKey?: string
  productsKey: string
  priceKey: string
  /** Prior period estimate (nullable per row) — dashed line */
  pricePrevKey: string
  productsLabel: string
  priceLabel: string
  prevLineLabel: string
  height?: number
}

/** Bars: product count + price index; line: prior snapshot–scaled price index (per category). */
export function CategoryPerformanceComboChart({
  data,
  nameKey = 'name',
  productsKey,
  priceKey,
  pricePrevKey,
  productsLabel,
  priceLabel,
  prevLineLabel,
  height = 260,
}: CategoryComboProps) {
  const theme = useChartTheme()
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 8, right: 14, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={theme.grid} vertical={false} />
        <XAxis
          dataKey={nameKey}
          tick={{ fontSize: 10, fill: theme.axisTick }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          yAxisId="left"
          tick={{ fontSize: 10, fill: theme.axisTick }}
          axisLine={false}
          tickLine={false}
          width={38}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          tick={{ fontSize: 10, fill: theme.axisTick }}
          axisLine={false}
          tickLine={false}
          width={38}
        />
        <Tooltip contentStyle={chartTooltipStyle(theme, { fontSize: 11 })} />
        <Legend wrapperStyle={{ fontSize: 11 }} iconSize={8} />
        <Bar
          yAxisId="left"
          dataKey={productsKey}
          name={productsLabel}
          fill={theme.interactive}
          radius={[4, 4, 0, 0]}
          maxBarSize={26}
        />
        <Bar
          yAxisId="right"
          dataKey={priceKey}
          name={priceLabel}
          fill={theme.trendUp}
          radius={[4, 4, 0, 0]}
          maxBarSize={26}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey={pricePrevKey}
          name={prevLineLabel}
          stroke={theme.axisLabel}
          strokeWidth={2}
          strokeDasharray="6 5"
          dot={{ r: 2.5, fill: theme.axisLabel }}
          activeDot={{ r: 4 }}
          connectNulls
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
