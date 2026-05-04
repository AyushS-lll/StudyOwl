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

interface TeacherMetrics {
  total_students: number
  sessions_today: number
  average_success_rate: number
  pending_alerts: number
}

interface StudentSummary {
  id: string
  name: string
  grade_level: string
}

interface StudentProgress {
  subjects: Array<{ name: string; sessions: number; success_rate: number }>
  recent_sessions: Array<{ id: string; question: string; subject: string; resolved: boolean; started_at: string }>
}

export const TeacherDash: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertSession[]>([])
  const [metrics, setMetrics] = useState<TeacherMetrics | null>(null)
  const [students, setStudents] = useState<StudentSummary[]>([])
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null)
  const [selectedStudentProgress, setSelectedStudentProgress] = useState<StudentProgress | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingStudent, setLoadingStudent] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const [alertResponse, metricsResponse, studentListResponse] = await Promise.all([
          api.getAlerts(),
          api.getTeacherMetrics(),
          api.getStudentList(),
        ])
        setAlerts(alertResponse.pending_alerts)
        setMetrics(metricsResponse)
        setStudents(studentListResponse.students)
        if (studentListResponse.students.length > 0) {
          setSelectedStudentId(studentListResponse.students[0].id)
        }
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }

    loadDashboard()
  }, [])

  useEffect(() => {
    if (!selectedStudentId) {
      return
    }

    const loadStudentProgress = async () => {
      setLoadingStudent(true)
      try {
        const progress = await api.getStudentProgress(selectedStudentId)
        setSelectedStudentProgress(progress)
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoadingStudent(false)
      }
    }

    loadStudentProgress()
  }, [selectedStudentId])

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🦉 Teacher Dashboard
          </h1>
          <p className="text-gray-600">Monitor student progress and help when needed</p>
        </header>

        <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">📚 Student Roster</h2>
              {loading ? (
                <p className="text-gray-600">Loading students...</p>
              ) : students.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-600 text-lg">No students found.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {students.map((student) => (
                    <button
                      key={student.id}
                      onClick={() => setSelectedStudentId(student.id)}
                      className={`block w-full rounded-2xl border px-4 py-3 text-left transition ${selectedStudentId === student.id ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 bg-white hover:border-indigo-300 hover:bg-slate-50'}`}
                    >
                      <p className="font-semibold text-gray-900">{student.name}</p>
                      <p className="text-sm text-gray-500">{student.grade_level}</p>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">⚠️ Alerts</h2>
              {loading ? (
                <p className="text-gray-600">Loading alerts...</p>
              ) : alerts.length === 0 ? (
                <p className="text-gray-600">No active alerts right now.</p>
              ) : (
                <div className="space-y-4">
                  {alerts.map((alert) => (
                    <div key={alert.id} className="rounded-2xl border border-yellow-200 bg-yellow-50 p-4">
                      <p className="font-semibold text-gray-900">{alert.student_name}</p>
                      <p className="text-sm text-gray-600 mt-1">Q: {alert.question.substring(0, 100)}...</p>
                      <p className="text-sm text-gray-600 mt-1">Hint Level: {alert.hint_level}/3 | Failed: {alert.fails_at_level}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">📊 Class Overview</h2>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center rounded-2xl bg-slate-50 p-4">
                  <p className="text-3xl font-bold text-indigo-600">{metrics ? metrics.total_students : '—'}</p>
                  <p className="text-gray-600 text-sm">Total Students</p>
                </div>
                <div className="text-center rounded-2xl bg-slate-50 p-4">
                  <p className="text-3xl font-bold text-green-600">{metrics ? metrics.sessions_today : '—'}</p>
                  <p className="text-gray-600 text-sm">Sessions Today</p>
                </div>
                <div className="text-center rounded-2xl bg-slate-50 p-4">
                  <p className="text-3xl font-bold text-blue-600">{metrics ? `${metrics.average_success_rate}%` : '—'}</p>
                  <p className="text-gray-600 text-sm">Success Rate</p>
                </div>
              </div>
              <div className="mt-4 rounded-2xl bg-white p-4 border border-slate-200 text-center text-sm text-slate-600">
                Pending alerts: {metrics ? metrics.pending_alerts : '—'}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between gap-4 mb-4">
                <div>
                  <h2 className="text-xl font-bold text-gray-800">Student Analytics</h2>
                  <p className="text-sm text-gray-500">View details for the selected student.</p>
                </div>
                <span className="rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold text-indigo-700">
                  {selectedStudentId ? 'Student selected' : 'Pick a student'}
                </span>
              </div>

              {loadingStudent ? (
                <p className="text-gray-600">Loading student progress...</p>
              ) : selectedStudentProgress ? (
                <div className="space-y-5">
                  <div>
                    <h3 className="text-sm uppercase tracking-wide text-slate-500">Subjects</h3>
                    <div className="mt-3 space-y-3">
                      {selectedStudentProgress.subjects.map((subject) => (
                        <div key={subject.name} className="rounded-2xl bg-slate-50 p-4">
                          <div className="flex items-center justify-between gap-4">
                            <p className="font-semibold text-slate-900">{subject.name}</p>
                            <p className="text-sm text-slate-600">{subject.sessions} sessions</p>
                          </div>
                          <div className="mt-2 h-2 rounded-full bg-white">
                            <div className="h-full rounded-full bg-indigo-600" style={{ width: `${subject.success_rate * 100}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm uppercase tracking-wide text-slate-500">Recent Sessions</h3>
                    <div className="mt-3 space-y-3">
                      {selectedStudentProgress.recent_sessions.map((session) => (
                        <div key={session.id} className="rounded-2xl border border-slate-200 bg-white p-4">
                          <p className="font-semibold text-slate-900">{session.question}</p>
                          <p className="text-sm text-slate-500">{session.subject} • {session.resolved ? 'Resolved' : 'Open'}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-gray-600">Select a student to see their analytics.</p>
              )}
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error.includes("Authentication token missing")
              ? "Your session expired or the login token is missing. Please log out and sign in again."
              : error}
          </div>
        )}
      </div>
    </div>
  )
}

export default TeacherDash
