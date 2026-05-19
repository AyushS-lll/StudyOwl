import { useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

interface FormData {
  email: string
  password: string
  name: string
  grade_level: string
  role: 'student' | 'teacher'
}

const HOME_FOR_ROLE = { student: '/student', teacher: '/teacher' } as const

function readFromState(state: unknown): string | null {
  if (state && typeof state === 'object' && 'from' in state) {
    const from = (state as { from?: unknown }).from
    if (typeof from === 'string' && from.startsWith('/')) return from
  }
  return null
}

export function Login() {
  const { user, login, signup, status } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login')
  const [formData, setFormData] = useState<FormData>({
    email: '',
    password: '',
    name: '',
    grade_level: '',
    role: 'student',
  })
  const [error, setError] = useState<string | null>(null)

  // Already logged in? Bounce to the home page for the role.
  if (user) {
    return <Navigate to={HOME_FOR_ROLE[user.role]} replace />
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      const next = authMode === 'login'
        ? await login({
            email: formData.email,
            password: formData.password,
            role: formData.role,
          })
        : await signup({
            email: formData.email,
            password: formData.password,
            name: formData.name,
            grade_level: formData.grade_level,
            role: formData.role,
          })
      const fromUrl = readFromState(location.state)
      navigate(fromUrl ?? HOME_FOR_ROLE[next.role], { replace: true })
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const isSubmitting = status === 'authenticating'

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-indigo-950 to-sky-900 text-white overflow-hidden relative">
      <div className="pointer-events-none absolute inset-0 opacity-30">
        <div className="absolute -left-10 top-10 text-[5rem] text-white/10">∑</div>
        <div className="absolute right-8 top-24 text-[4rem] text-white/10">π</div>
        <div className="absolute left-1/2 top-1/3 text-[6rem] text-white/10">√</div>
        <div className="absolute right-20 bottom-28 text-[5rem] text-white/10">∞</div>
        <div className="absolute left-10 bottom-10 text-[4rem] text-white/10">α</div>
      </div>

      <div className="relative max-w-5xl mx-auto px-6 py-12 lg:flex lg:items-center lg:gap-12">
        <div className="lg:w-1/2 space-y-6">
          <div className="inline-flex items-center gap-3 rounded-full bg-white/10 px-4 py-2 text-sm text-slate-100 backdrop-blur-sm">
            <span className="text-xl">🦉</span>
            Learn faster with Socratic hints and smart feedback.
          </div>
          <div>
            <h1 className="text-5xl font-extrabold tracking-tight">
              StudyOwl makes homework smarter.
            </h1>
            <p className="mt-4 max-w-xl text-lg text-slate-200">
              Get step-by-step guidance, view your progress, and switch between student or teacher dashboards with a single login.
            </p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-300 mb-3">Choose your workspace</p>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setFormData({ ...formData, role: 'student' })}
                className={`rounded-3xl p-5 shadow-lg border transition text-left ${formData.role === 'student' ? 'border-indigo-400 bg-white/10 text-white' : 'border-white/10 bg-white/5 text-slate-200 hover:bg-white/10'}`}
              >
                <p className="text-2xl font-bold">Student</p>
                <p className="mt-2 text-slate-200">Practice questions, collect hints, and track your learning gains.</p>
              </button>
              <button
                type="button"
                onClick={() => setFormData({ ...formData, role: 'teacher' })}
                className={`rounded-3xl p-5 shadow-lg border transition text-left ${formData.role === 'teacher' ? 'border-indigo-400 bg-white/10 text-white' : 'border-white/10 bg-white/5 text-slate-200 hover:bg-white/10'}`}
              >
                <p className="text-2xl font-bold">Teacher</p>
                <p className="mt-2 text-slate-200">Monitor classroom alerts, review student progress, and identify struggling learners.</p>
              </button>
            </div>
          </div>
        </div>

        <div className="mt-10 lg:mt-0 lg:w-1/2">
          <div className="rounded-3xl bg-slate-900/95 border border-white/10 p-8 shadow-2xl backdrop-blur-sm">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-3xl font-bold">{authMode === 'login' ? 'Welcome back' : 'Create account'}</h2>
                <p className="text-slate-400">Sign in as a student or teacher to continue.</p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setAuthMode(authMode === 'login' ? 'signup' : 'login')
                  setError(null)
                }}
                className="rounded-full bg-indigo-500 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-400 transition"
              >
                {authMode === 'login' ? 'Switch to sign up' : 'Switch to login'}
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, role: 'student' })}
                  className={`rounded-2xl border px-4 py-3 text-sm font-semibold transition ${formData.role === 'student' ? 'border-indigo-400 bg-indigo-500 text-white' : 'border-white/20 bg-white/5 text-slate-200 hover:bg-white/10'}`}
                >
                  Student
                </button>
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, role: 'teacher' })}
                  className={`rounded-2xl border px-4 py-3 text-sm font-semibold transition ${formData.role === 'teacher' ? 'border-indigo-400 bg-indigo-500 text-white' : 'border-white/20 bg-white/5 text-slate-200 hover:bg-white/10'}`}
                >
                  Teacher
                </button>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-200 mb-1">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  className="w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-slate-100 outline-none ring-2 ring-transparent transition focus:border-indigo-400 focus:ring-indigo-500/30"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-200 mb-1">Password</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  className="w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-slate-100 outline-none ring-2 ring-transparent transition focus:border-indigo-400 focus:ring-indigo-500/30"
                />
              </div>

              {authMode === 'signup' && (
                <>
                  <div>
                    <label className="block text-sm font-semibold text-slate-200 mb-1">Full Name</label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                      className="w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-slate-100 outline-none ring-2 ring-transparent transition focus:border-indigo-400 focus:ring-indigo-500/30"
                    />
                  </div>

                  {formData.role === 'student' && (
                    <div>
                      <label className="block text-sm font-semibold text-slate-200 mb-1">Grade Level</label>
                      <input
                        type="text"
                        placeholder="e.g., Grade 7, University"
                        value={formData.grade_level}
                        onChange={(e) => setFormData({ ...formData, grade_level: e.target.value })}
                        required
                        className="w-full rounded-2xl border border-white/10 bg-slate-950/90 px-4 py-3 text-slate-100 outline-none ring-2 ring-transparent transition focus:border-indigo-400 focus:ring-indigo-500/30"
                      />
                    </div>
                  )}
                </>
              )}

              {error && (
                <div className="rounded-2xl border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-200">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full rounded-2xl bg-gradient-to-r from-indigo-500 to-sky-500 py-3 text-sm font-semibold text-white shadow-xl shadow-slate-900/20 hover:from-indigo-400 hover:to-sky-400 transition disabled:opacity-60"
              >
                {isSubmitting ? 'Signing in…' : `${authMode === 'login' ? 'Log in' : 'Sign up'} as ${formData.role}`}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
