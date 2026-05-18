import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { api } from '../api/studyowl'
import type { LoginRequest, SignUpRequest, TokenResponse } from '../api/studyowl'

const TOKEN_KEY = 'studyowl_token'
const ROLE_KEY = 'studyowl_role'
const USER_ID_KEY = 'studyowl_user_id'
const USER_NAME_KEY = 'studyowl_user_name'

export type UserRole = 'student' | 'teacher'

export interface AuthUser {
  id: string
  role: UserRole
  name: string | null
}

interface AuthContextValue {
  user: AuthUser | null
  token: string | null
  status: 'idle' | 'authenticating'
  login: (body: LoginRequest) => Promise<AuthUser>
  signup: (body: SignUpRequest) => Promise<AuthUser>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

function readPersisted(): { user: AuthUser | null; token: string | null } {
  const token = localStorage.getItem(TOKEN_KEY)
  const id = localStorage.getItem(USER_ID_KEY)
  const role = localStorage.getItem(ROLE_KEY) as UserRole | null
  const name = localStorage.getItem(USER_NAME_KEY)
  if (!token || !id || (role !== 'student' && role !== 'teacher')) {
    return { user: null, token: null }
  }
  return { user: { id, role, name }, token }
}

function persist(token: string, user: AuthUser) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_ID_KEY, user.id)
  localStorage.setItem(ROLE_KEY, user.role)
  if (user.name) localStorage.setItem(USER_NAME_KEY, user.name)
  else localStorage.removeItem(USER_NAME_KEY)
}

function clearPersisted() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_ID_KEY)
  localStorage.removeItem(ROLE_KEY)
  localStorage.removeItem(USER_NAME_KEY)
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const initial = readPersisted()
  const [user, setUser] = useState<AuthUser | null>(initial.user)
  const [token, setToken] = useState<string | null>(initial.token)
  const [status, setStatus] = useState<'idle' | 'authenticating'>('idle')

  const apply = useCallback((response: TokenResponse, fallbackName: string | null) => {
    // Backend may or may not return `name` depending on deploy; fall back to
    // the name the user typed in signup, or null.
    const responseName = (response as TokenResponse & { name?: string }).name ?? null
    const nextUser: AuthUser = {
      id: response.user_id,
      role: response.role,
      name: responseName ?? fallbackName,
    }
    persist(response.access_token, nextUser)
    setToken(response.access_token)
    setUser(nextUser)
    return nextUser
  }, [])

  const login = useCallback(
    async (body: LoginRequest) => {
      setStatus('authenticating')
      try {
        const result = await api.login(body)
        return apply(result, null)
      } finally {
        setStatus('idle')
      }
    },
    [apply],
  )

  const signup = useCallback(
    async (body: SignUpRequest) => {
      setStatus('authenticating')
      try {
        const result = await api.signup(body)
        return apply(result, body.name)
      } finally {
        setStatus('idle')
      }
    },
    [apply],
  )

  const logout = useCallback(() => {
    clearPersisted()
    setToken(null)
    setUser(null)
  }, [])

  // Cross-tab sync: when another tab removes the token (logout) or replaces it
  // (login as a different user), mirror that here so the two tabs don't drift.
  useEffect(() => {
    const handler = (e: StorageEvent) => {
      if (e.key !== TOKEN_KEY) return
      if (e.newValue === null) {
        setToken(null)
        setUser(null)
      } else {
        const refreshed = readPersisted()
        setToken(refreshed.token)
        setUser(refreshed.user)
      }
    }
    window.addEventListener('storage', handler)
    return () => window.removeEventListener('storage', handler)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ user, token, status, login, signup, logout }),
    [user, token, status, login, signup, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
