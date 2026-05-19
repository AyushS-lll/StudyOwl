import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface ChartData {
  subject: string
  sessions: number
  success_rate: number
}

interface ProgressChartProps {
  data: ChartData[]
}

export const ProgressChart: React.FC<ProgressChartProps> = ({ data }) => {
  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-600">
        <p>Start a session to see your progress breakdown</p>
      </div>
    )
  }

  const formatTick = (value: string) =>
    value.length > 8 ? `${value.slice(0, 8)}…` : value

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart
        data={data}
        margin={{ top: 8, right: 8, left: -16, bottom: 0 }}
        barCategoryGap="22%"
      >
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="subject"
          tick={{ fontSize: 11, fill: '#475569' }}
          tickFormatter={formatTick}
          interval={0}
          tickMargin={6}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: '#475569' }}
          width={32}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{ borderRadius: 12, fontSize: 12, borderColor: '#e0e7ff' }}
          cursor={{ fill: 'rgba(99, 102, 241, 0.06)' }}
        />
        <Legend
          wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
          iconType="circle"
          iconSize={8}
        />
        <Bar dataKey="sessions" fill="#6366f1" name="Sessions" radius={[6, 6, 0, 0]} />
        <Bar dataKey="success_rate" fill="#a5b4fc" name="Success Rate %" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export default ProgressChart
