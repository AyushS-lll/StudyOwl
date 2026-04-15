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

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="subject" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="sessions" fill="#8b7355" name="Sessions" />
        <Bar dataKey="success_rate" fill="#d4a574" name="Success Rate %" />
      </BarChart>
    </ResponsiveContainer>
  )
}

export default ProgressChart
