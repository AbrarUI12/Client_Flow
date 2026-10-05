import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { getCurrentUser, loginRequest, logoutRequest } from './api'
import { AuthContext } from './authStore'
import type { AuthStatus } from './authStore'
import { clearAccessToken, getAccessToken, setAccessToken, UNAUTHORIZED_EVENT } from './session'
import type { AuthUser, LoginCredentials } from './types'

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [status, setStatus] = useState<AuthStatus>(() =>
    getAccessToken() ? 'loading' : 'anonymous',
  )

  const clearSession = useCallback(() => {
    clearAccessToken()
    // Cached records belong to the ending session and must never render for the next account.
    queryClient.clear()
    setUser(null)
    setStatus('anonymous')
  }, [queryClient])

  useEffect(() => {
    const handleUnauthorized = () => clearSession()
    window.addEventListener(UNAUTHORIZED_EVENT, handleUnauthorized)
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, handleUnauthorized)
  }, [clearSession])

  useEffect(() => {
    if (!getAccessToken()) {
      return
    }

    let active = true
    void getCurrentUser()
      .then((currentUser) => {
        if (active) {
          setUser(currentUser)
          setStatus('authenticated')
        }
      })
      .catch(() => {
        if (active) {
          clearSession()
        }
      })

    return () => {
      active = false
    }
  }, [clearSession])

  const login = useCallback(async (credentials: LoginCredentials) => {
    const token = await loginRequest(credentials)
    setAccessToken(token.access_token)

    try {
      const currentUser = await getCurrentUser()
      queryClient.clear()
      setUser(currentUser)
      setStatus('authenticated')
    } catch (error) {
      clearAccessToken()
      throw error
    }
  }, [queryClient])

  const logout = useCallback(async () => {
    try {
      if (getAccessToken()) {
        await logoutRequest()
      }
    } finally {
      clearSession()
    }
  }, [clearSession])

  const value = useMemo(
    () => ({ user, status, login, logout }),
    [user, status, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
