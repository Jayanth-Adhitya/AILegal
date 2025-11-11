"use client"

import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react'
import { API_BASE_URL } from '@/lib/api'

interface User {
  id: string
  email: string
  company_name: string
  company_id: string
  created_at: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<boolean>
  register: (email: string, password: string, companyName: string, companyId?: string) => Promise<boolean>
  logout: () => Promise<void>
  checkSession: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Check session on mount
  useEffect(() => {
    checkSession()
  }, [])

  const checkSession = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
        credentials: 'include'
      })

      if (response.ok) {
        const data = await response.json()
        setUser(data.user)
      } else {
        setUser(null)
      }
    } catch (err) {
      console.error('Session check failed:', err)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      setError(null)
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ email, password })
      })

      const data = await response.json()

      if (data.success) {
        setUser(data.user)
        return true
      } else {
        setError(data.error || 'Login failed')
        return false
      }
    } catch (err) {
      setError('Network error. Please try again.')
      return false
    }
  }

  const register = async (
    email: string,
    password: string,
    companyName: string,
    companyId?: string
  ): Promise<boolean> => {
    try {
      setError(null)
      const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          email,
          password,
          company_name: companyName,
          company_id: companyId
        })
      })

      const data = await response.json()

      if (data.success) {
        setUser(data.user)
        return true
      } else {
        setError(data.error || 'Registration failed')
        return false
      }
    } catch (err) {
      setError('Network error. Please try again.')
      return false
    }
  }

  const logout = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      })
      setUser(null)
    } catch (err) {
      console.error('Logout failed:', err)
      // Clear user even if logout fails
      setUser(null)
    }
  }

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    checkSession
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}