import { Link, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

/**
 * Authed-route shell: top navbar (greeting + logout) and an <Outlet /> for the
 * actual page. Wrapped around every route behind ProtectedRoute.
 */
export function Layout() {
  const { user, logout } = useAuth()
  const displayName = user?.name ?? (user?.role === 'teacher' ? 'Teacher' : 'Student')

  return (
    <div>
      <nav className="bg-indigo-900 text-white p-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <Link to="/" className="text-2xl font-bold">
            🦉 StudyOwl
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-sm text-indigo-100">Hi, {displayName} 👋</span>
            <button
              onClick={logout}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition"
            >
              Log Out
            </button>
          </div>
        </div>
      </nav>
      <Outlet />
    </div>
  )
}

export default Layout
