import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { getMe, apiLogin, apiRegister } from '../lib/api'
import type { User } from '../lib/types'

interface AuthCtx {
  user: User | null
  loading: boolean
  login: (u: string, p: string) => Promise<void>
  register: (u: string, p: string) => Promise<void>
  logout: () => void
}

const Ctx = createContext<AuthCtx | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser]       = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('kt_token')
    if (token) {
      getMe().then(setUser).catch(() => localStorage.removeItem('kt_token')).finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (username: string, password: string) => {
    const { token, user } = await apiLogin(username, password)
    localStorage.setItem('kt_token', token)
    setUser(user)
  }

  const register = async (username: string, password: string) => {
    const { token, user } = await apiRegister(username, password)
    localStorage.setItem('kt_token', token)
    setUser(user)
  }

  const logout = () => {
    localStorage.removeItem('kt_token')
    setUser(null)
  }

  return <Ctx.Provider value={{ user, loading, login, register, logout }}>{children}</Ctx.Provider>
}

export const useAuth = () => {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
