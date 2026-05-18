import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

/**
 * "/" index route. Sends the user to the right home page based on their role,
 * or to /login if no session is present.
 */
export function RouteResolver() {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return <Navigate to={user.role === 'teacher' ? '/teacher' : '/student'} replace />
}

export default RouteResolver
