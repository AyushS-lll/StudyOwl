import { Navigate, Outlet, useLocation } from 'react-router-dom'
import type { UserRole } from '../auth/AuthContext'
import { useAuth } from '../auth/AuthContext'

interface ProtectedRouteProps {
  requireRole?: UserRole
}

export function ProtectedRoute({ requireRole }: ProtectedRouteProps) {
  const { user } = useAuth()
  const location = useLocation()

  if (!user) {
    const from = `${location.pathname}${location.search}`
    return <Navigate to="/login" state={{ from }} replace />
  }

  if (requireRole && user.role !== requireRole) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}

export default ProtectedRoute
