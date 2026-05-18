import React, { useEffect, useState } from 'react'
import { api } from '../api/studyowl'
import type { TeacherAlert, TeacherMetricsResponse } from '../api/studyowl'

const SEVERITY_BADGE: Record<TeacherAlert['severity'], { label: string; classes: string }> = {
  high: { label: '🔴 HIGH', classes: 'bg-red-100 text-red-800 border-red-300' },
  medium: { label: '🟡 MED', classes: 'bg-amber-100 text-amber-800 border-amber-300' },
  low: { label: '🔵 LOW', classes: 'bg-sky-100 text-sky-800 border-sky-300' },
}

const REASON_LABEL: Record<TeacherAlert['reason_kind'], string> = {
  distress: 'Distress',
  repeated_failure: 'Stuck',
  inactivity: 'Inactive',
  legacy: 'Legacy',
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
  const [alerts, setAlerts] = useState<TeacherAlert[]>([])
  const [metrics, setMetrics] = useState<TeacherMetricsResponse | null>(null)
  const [students, setStudents] = useState<StudentSummary[]>([])
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null)
  const [selectedStudentProgress, setSelectedStudentProgress] = useState<StudentProgress | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingStudent, setLoadingStudent] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // In-flight ack/resolve to prevent double-clicks. Keyed by alert ID.
  const [actionInFlight, setActionInFlight] = useState<Record<string, boolean>>({})

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

  const handleAcknowledge = async (alert: TeacherAlert) => {
    if (actionInFlight[alert.id]) return
    setActionInFlight((m) => ({ ...m, [alert.id]: true }))
    // Optimistic: mark acknowledged locally before the round-trip.
    setAlerts((curr) =>
      curr.map((a) =>
        a.id === alert.id
          ? { ...a, acknowledged_at: new Date().toISOString(), acknowledged_by_name: 'you' }
          : a,
      ),
    )
    try {
      const fresh = await api.acknowledgeAlert(alert.id)
      setAlerts((curr) => curr.map((a) => (a.id === fresh.id ? fresh : a)))
    } catch (err) {
      // Roll back optimistic state on error.
      setAlerts((curr) =>
        curr.map((a) =>
          a.id === alert.id
            ? { ...a, acknowledged_at: alert.acknowledged_at, acknowledged_by_name: alert.acknowledged_by_name }
            : a,
        ),
      )
      setError((err as Error).message)
    } finally {
      setActionInFlight((m) => {
        const next = { ...m }
        delete next[alert.id]
        return next
      })
    }
  }

  const handleResolve = async (alert: TeacherAlert) => {
    if (actionInFlight[alert.id]) return
    setActionInFlight((m) => ({ ...m, [alert.id]: true }))
    // Optimistic: remove from the unresolved list immediately.
    setAlerts((curr) => curr.filter((a) => a.id !== alert.id))
    try {
      await api.resolveAlert(alert.id)
      // Decrement the pending counter in metrics, optimistically.
      setMetrics((m) => (m ? { ...m, pending_alerts: Math.max(0, m.pending_alerts - 1) } : m))
    } catch (err) {
      // Roll back: re-add the alert.
      setAlerts((curr) => [alert, ...curr])
      setError((err as Error).message)
    } finally {
      setActionInFlight((m) => {
        const next = { ...m }
        delete next[alert.id]
        return next
      })
    }
  }

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
                  {alerts.map((alert) => {
                    const badge = SEVERITY_BADGE[alert.severity]
                    const busy = !!actionInFlight[alert.id]
                    return (
                      <div
                        key={alert.id}
                        className="rounded-2xl border border-yellow-200 bg-yellow-50 p-4 space-y-2"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <p className="font-semibold text-gray-900">{alert.student_name}</p>
                          <span
                            className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${badge.classes}`}
                            title={`${REASON_LABEL[alert.reason_kind]}: ${alert.reason_text}`}
                          >
                            {badge.label}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">
                          {REASON_LABEL[alert.reason_kind]} · Hint {alert.hint_level}/3 · {alert.fails_at_level} fails
                        </p>
                        <p className="text-sm text-gray-700">
                          Q: {alert.question.substring(0, 120)}{alert.question.length > 120 ? '…' : ''}
                        </p>
                        {alert.notification_status === 'failed' && (
                          <p className="text-xs text-red-700">⚠️ Delivery failed</p>
                        )}
                        <div className="flex items-center justify-between gap-2 pt-1">
                          <span className="text-xs text-gray-500">
                            {alert.acknowledged_at
                              ? `Ack'd by ${alert.acknowledged_by_name ?? 'someone'}`
                              : 'Not yet acknowledged'}
                          </span>
                          <div className="flex gap-2">
                            {!alert.acknowledged_at && (
                              <button
                                disabled={busy}
                                onClick={() => handleAcknowledge(alert)}
                                className="text-xs px-3 py-1 rounded-full bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition"
                              >
                                {busy ? '…' : 'Acknowledge'}
                              </button>
                            )}
                            <button
                              disabled={busy}
                              onClick={() => handleResolve(alert)}
                              className="text-xs px-3 py-1 rounded-full bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition"
                            >
                              {busy ? '…' : 'Resolve'}
                            </button>
                          </div>
                        </div>
                      </div>
                    )
                  })}
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
