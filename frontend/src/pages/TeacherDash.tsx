import React, { useEffect, useState } from 'react'
import { api } from '../api/studyowl'

interface AlertSession {
  id: string
  student_name: string
  question: string
  hint_level: number
  fails_at_level: number
  started_at: string
}

export const TeacherDash: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertSession[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Placeholder: In a real app, this would fetch alerts from the API
    // For now, show a mock interface
    setLoading(false)
    setAlerts([])
  }, [])

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🦉 Teacher Dashboard
          </h1>
          <p className="text-gray-600">Monitor student progress and help when needed</p>
        </header>

        <div className="grid gap-6">
          {/* Active Alerts */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              ⚠️ Students Needing Help
            </h2>

            {loading ? (
              <p className="text-gray-600">Loading alerts...</p>
            ) : alerts.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-600 text-lg">
                  ✨ All students are doing great!
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="border-l-4 border-yellow-500 bg-yellow-50 p-4 rounded"
                  >
                    <p className="font-semibold text-gray-900">
                      {alert.student_name}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      Q: {alert.question.substring(0, 100)}...
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      Hint Level: {alert.hint_level}/3 | Failed: {alert.fails_at_level}
                    </p>
                    <button className="mt-3 px-3 py-1 bg-yellow-600 text-white rounded hover:bg-yellow-700 text-sm">
                      View Session
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Class Statistics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              📊 Class Overview
            </h2>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-indigo-600">0</p>
                <p className="text-gray-600 text-sm">Students Online</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-green-600">0</p>
                <p className="text-gray-600 text-sm">Sessions Today</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-blue-600">0%</p>
                <p className="text-gray-600 text-sm">Success Rate</p>
              </div>
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}
      </div>
    </div>
  )
}

export default TeacherDash
