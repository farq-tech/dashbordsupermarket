'use client'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { chartTooltipStyle } from '@/lib/chartTheme'
import { useChartTheme } from '@/lib/useChartTheme'

interface ScatterPoint {
  x: number
  y: number
  name?: string
  tag?: string
}

interface ScatterProps {
  data: ScatterPoint[]
  height?: number
  xLabel?: string
  yLabel?: string
}

export function PriceScatterChart({ data, height = 300, xLabel = 'Market Avg', yLabel = 'Your Price' }: ScatterProps) {
  const theme = useChartTheme()
  const tagColor = (tag: string | undefined) =>
    (tag && theme.scatterTags[tag as keyof typeof theme.scatterTags]) || theme.interactive

  // Compute parity line domain from actual data so y = x always spans the visible range
  const maxVal = data.length > 0
    ? Math.ceil(Math.max(...data.map(d => Math.max(d.x, d.y))) * 1.1)
    : 200
  const paritySegment: [{ x: number; y: number }, { x: number; y: number }] = [
    { x: 0, y: 0 },
    { x: maxVal, y: maxVal },
  ]

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={theme.grid} vertical={false} />
        <XAxis
          dataKey="x"
          name={xLabel}
          type="number"
          tick={{ fontSize: 11, fill: theme.axisTick }}
          axisLine={false}
          tickLine={false}
          label={{ value: xLabel, position: 'bottom', offset: 0, fontSize: 11, fill: theme.axisLabel }}
        />
        <YAxis
          dataKey="y"
          name={yLabel}
          type="number"
          tick={{ fontSize: 11, fill: theme.axisTick }}
          axisLine={false}
          tickLine={false}
          label={{ value: yLabel, angle: -90, position: 'insideLeft', offset: 10, fontSize: 11, fill: theme.axisLabel }}
        />
        <Tooltip
          contentStyle={chartTooltipStyle(theme, { fontSize: 11 })}
          cursor={{ strokeDasharray: '3 3' }}
        />
        {/* y = x parity line — points above the line are priced above market, below are cheaper */}
        <ReferenceLine
          stroke={theme.grid}
          strokeDasharray="5 4"
          strokeWidth={1.5}
          segment={paritySegment}
        />
        <Scatter
          data={data}
          fill={theme.interactive}
          opacity={0.7}
          shape={(props: unknown) => {
            const { cx, cy, payload } = props as { cx: number; cy: number; payload: ScatterPoint }
            const color = tagColor(payload?.tag)
            return <circle cx={cx} cy={cy} r={4} fill={color} fillOpacity={0.75} />
          }}
        />
      </ScatterChart>
    </ResponsiveContainer>
  )
}
