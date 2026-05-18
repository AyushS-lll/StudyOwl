import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import { ProtectedRoute } from './router/ProtectedRoute'
import { RouteResolver } from './router/RouteResolver'
import Layout from './components/Layout'
import Login from './pages/Login'
import StudentChat from './pages/StudentChat'
import TeacherDash from './pages/TeacherDash'
import NotFound from './pages/NotFound'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public */}
          <Route path="/" element={<RouteResolver />} />
          <Route path="/login" element={<Login />} />

          {/* Student-only */}
          <Route element={<ProtectedRoute requireRole="student" />}>
            <Route element={<Layout />}>
              <Route path="/student" element={<StudentChat />} />
            </Route>
          </Route>

          {/* Teacher-only */}
          <Route element={<ProtectedRoute requireRole="teacher" />}>
            <Route element={<Layout />}>
              <Route path="/teacher" element={<TeacherDash />} />
              <Route path="/teacher/students/:studentId" element={<TeacherDash />} />
            </Route>
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
