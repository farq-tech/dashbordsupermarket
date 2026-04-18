'use client'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell
} from 'recharts'

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
  data, dataKey, nameKey = 'name', color = '#1b59f8',
  height = 240, showGrid = true, unit = '', colors,
}: BarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e4e5e7" vertical={false} />}
        <XAxis
          dataKey={nameKey}
          tick={{ fontSize: 11, fill: '#838383' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: '#838383' }}
          axisLine={false}
          tickLine={false}
          tickFormatter={v => `${v}${unit}`}
        />
        <Tooltip
          contentStyle={{
            borderRadius: 12,
            border: '1px solid #eff0f6',
            fontSize: 12,
            boxShadow: '0 5px 20px rgba(0,0,0,0.05)',
          }}
          formatter={(v: unknown) => [`${v}${unit}`, '']}
        />
        <Bar dataKey={dataKey} radius={[6, 6, 0, 0]} maxBarSize={48}>
          {colors
            ? data.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)
            : <Cell fill={color} />
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
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e4e5e7" vertical={false} />
        <XAxis dataKey={nameKey} tick={{ fontSize: 11, fill: '#838383' }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 11, fill: '#838383' }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{
            borderRadius: 12,
            border: '1px solid #eff0f6',
            fontSize: 12,
            boxShadow: '0 5px 20px rgba(0,0,0,0.05)',
          }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {keys.map(k => (
          <Bar key={k.dataKey} dataKey={k.dataKey} name={k.name} fill={k.color} radius={[6, 6, 0, 0]} maxBarSize={40} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}
