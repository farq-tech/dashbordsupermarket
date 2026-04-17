'use client'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface PieChartProps {
  data: { name: string; value: number; color: string }[]
  height?: number
  innerRadius?: number
  outerRadius?: number
  showLegend?: boolean
}

export function SimplePieChart({
  data, height = 240, innerRadius = 60, outerRadius = 90, showLegend = true,
}: PieChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={innerRadius}
          outerRadius={outerRadius}
          paddingAngle={2}
          dataKey="value"
        >
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ borderRadius: 8, border: '1px solid #e4ebe6', fontSize: 12 }}
          formatter={(v: unknown) => [`${v}`, '']}
        />
        {showLegend && (
          <Legend
            wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
            iconType="circle"
            iconSize={8}
          />
        )}
      </PieChart>
    </ResponsiveContainer>
  )
}
