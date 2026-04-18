'use client'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

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

const TAG_COLORS: Record<string, string> = {
  overpriced: '#ff3e13',
  underpriced: '#1fe08f',
  competitive: '#1b59f8',
  opportunity: '#ca8a04',
  risk: '#ea580c',
  not_stocked: '#9ca3af',
}

export function PriceScatterChart({ data, height = 300, xLabel = 'Market Avg', yLabel = 'Your Price' }: ScatterProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e4e5e7" vertical={false} />
        <XAxis
          dataKey="x"
          name={xLabel}
          type="number"
          tick={{ fontSize: 11, fill: '#838383' }}
          axisLine={false}
          tickLine={false}
          label={{ value: xLabel, position: 'bottom', offset: 0, fontSize: 11, fill: '#9098a3' }}
        />
        <YAxis
          dataKey="y"
          name={yLabel}
          type="number"
          tick={{ fontSize: 11, fill: '#838383' }}
          axisLine={false}
          tickLine={false}
          label={{ value: yLabel, angle: -90, position: 'insideLeft', offset: 10, fontSize: 11, fill: '#9098a3' }}
        />
        <Tooltip
          contentStyle={{
            borderRadius: 12,
            border: '1px solid #eff0f6',
            fontSize: 11,
            boxShadow: '0 5px 20px rgba(0,0,0,0.05)',
          }}
          cursor={{ strokeDasharray: '3 3' }}
        />
        <ReferenceLine
          y={0}
          stroke="#e4e5e7"
          strokeDasharray="0"
          segment={[{ x: 0, y: 0 }, { x: 200, y: 200 }]}
        />
        <Scatter
          data={data}
          fill="#1b59f8"
          opacity={0.7}
          shape={(props: unknown) => {
            const { cx, cy, payload } = props as { cx: number; cy: number; payload: ScatterPoint }
            const color = TAG_COLORS[(payload as ScatterPoint).tag ?? ''] ?? '#1b59f8'
            return <circle cx={cx} cy={cy} r={4} fill={color} fillOpacity={0.75} />
          }}
        />
      </ScatterChart>
    </ResponsiveContainer>
  )
}
