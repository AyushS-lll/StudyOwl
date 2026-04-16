import React, { useState } from 'react'
import { api } from './api/studyowl'
import StudentChat from './pages/StudentChat'
import TeacherDash from './pages/TeacherDash'

// Type for form data
interface FormData {
  email: string
  password: string
  name: string
  grade_level: string
  role: string
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('studyowl_token'))
  const [userRole, setUserRole] = useState<'student' | 'teacher'>('student')
  const [showAuthForm, setShowAuthForm] = useState(!isLoggedIn)
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login')
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    grade_level: '',
    role: 'student',
  })

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (authMode === 'login') {
        await api.login({
          email: formData.email,
          password: formData.password,
        })
      } else {
        await api.signup({
          email: formData.email,
          password: formData.password,
          name: formData.name,
          grade_level: formData.grade_level,
          role: formData.role as 'student' | 'teacher',
        })
      }
      setUserRole(formData.role as 'student' | 'teacher')
      setIsLoggedIn(true)
      setShowAuthForm(false)
    } catch (error) {
      alert((error as Error).message)
    }
  }

  const handleLogout = () => {
    api.logout()
    setIsLoggedIn(false)
    setShowAuthForm(true)
    setFormData({
      email: '',
      password: '',
      name: '',
      grade_level: '',
      role: 'student',
    })
  }

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
          <h1 className="text-3xl font-bold text-indigo-900 text-center mb-6">
            🦉 StudyOwl
          </h1>

          <form onSubmit={handleAuth} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                required
                className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                required
                className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            {authMode === 'signup' && (
              <>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                    required
                    className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">
                    Grade Level
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., Grade 7, University"
                    value={formData.grade_level}
                    onChange={(e) =>
                      setFormData({ ...formData, grade_level: e.target.value })
                    }
                    required
                    className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">
                    I am a
                  </label>
                  <select
                    value={formData.role}
                    onChange={(e) =>
                      setFormData({ ...formData, role: e.target.value })
                    }
                    className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="student">Student</option>
                    <option value="teacher">Teacher</option>
                  </select>
                </div>
              </>
            )}

            <button
              type="submit"
              className="w-full bg-indigo-600 text-white py-2 rounded-lg font-semibold hover:bg-indigo-700 transition"
            >
              {authMode === 'login' ? 'Log In' : 'Sign Up'}
            </button>
          </form>

          <p className="text-center text-sm text-gray-600 mt-4">
            {authMode === 'login'
              ? "Don't have an account? "
              : 'Already have an account? '}
            <button
              onClick={() => {
                setAuthMode(authMode === 'login' ? 'signup' : 'login')
              }}
              className="text-indigo-600 hover:text-indigo-700 font-semibold"
            >
              {authMode === 'login' ? 'Sign up' : 'Log in'}
            </button>
          </p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <nav className="bg-indigo-900 text-white p-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">🦉 StudyOwl</h1>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition"
          >
            Log Out
          </button>
        </div>
      </nav>

      {userRole === 'student' ? <StudentChat /> : <TeacherDash />}
    </div>
  )
}

export default App
